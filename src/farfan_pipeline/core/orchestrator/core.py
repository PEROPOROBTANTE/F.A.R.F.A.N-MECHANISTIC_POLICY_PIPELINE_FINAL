"""Clean Orchestrator - Versión Completa y Funcional

Orquestador de 11 fases con toda la funcionalidad real preservada.
Sin simplificaciones, sin placeholders.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict, is_dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, TypeVar, ParamSpec

logger = logging.getLogger(__name__)

# Configuración de ambiente
EXPECTED_QUESTION_COUNT = int(os.getenv("EXPECTED_QUESTION_COUNT", "305"))
EXPECTED_METHOD_COUNT = int(os.getenv("EXPECTED_METHOD_COUNT", "416"))
PHASE_TIMEOUT_DEFAULT = int(os.getenv("PHASE_TIMEOUT_SECONDS", "300"))
P01_EXPECTED_CHUNK_COUNT = 60
TIMEOUT_SYNC_PHASES: set[int] = {1}

P = ParamSpec("P")
T = TypeVar("T")


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class Evidence:
    """Contenedor de evidencia para resultados de ejecución."""
    modality: str
    elements: list[Any] = field(default_factory=list)
    raw_results: dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseResult:
    """Resultado de una fase de orquestación."""
    success: bool
    phase_id: str
    data: Any
    error: Exception | None
    duration_ms: float
    mode: str
    aborted: bool = False


@dataclass
class MicroQuestionRun:
    """Resultado de ejecutar una micro-pregunta."""
    question_id: str
    question_global: int
    base_slot: str
    metadata: dict[str, Any]
    evidence: Evidence | None
    error: str | None = None
    duration_ms: float | None = None
    aborted: bool = False


@dataclass
class ScoredMicroQuestion:
    """Micro-pregunta con score asignado."""
    question_id: str
    question_global: int
    base_slot: str
    score: float | None
    normalized_score: float | None
    quality_level: str | None
    evidence: Evidence | None
    scoring_details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


# ============================================================================
# MECANISMO DE ABORT
# ============================================================================

class AbortRequested(RuntimeError):
    """Excepción lanzada cuando se activa un abort."""
    pass


class AbortSignal:
    """Señal de abort thread-safe compartida entre fases."""
    
    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._reason: str | None = None
        self._timestamp: datetime | None = None
    
    def abort(self, reason: str) -> None:
        """Activar abort con razón y timestamp."""
        if not reason:
            reason = "Abort requested"
        with self._lock:
            if not self._event.is_set():
                self._event.set()
                self._reason = reason
                self._timestamp = datetime.utcnow()
                logger.warning(f"Abort activado: {reason}")
    
    def is_aborted(self) -> bool:
        """Verificar si está abortado."""
        return self._event.is_set()
    
    def get_reason(self) -> str | None:
        """Obtener razón del abort."""
        with self._lock:
            return self._reason
    
    def get_timestamp(self) -> datetime | None:
        """Obtener timestamp del abort."""
        with self._lock:
            return self._timestamp
    
    def reset(self) -> None:
        """Limpiar la señal de abort."""
        with self._lock:
            self._event.clear()
            self._reason = None
            self._timestamp = None


# ============================================================================
# GESTIÓN DE RECURSOS
# ============================================================================

class ResourceLimits:
    """Guardián de recursos con predicción adaptativa de workers."""
    
    def __init__(
        self,
        max_memory_mb: float | None = 4096.0,
        max_cpu_percent: float = 85.0,
        max_workers: int = 32,
        min_workers: int = 4,
        hard_max_workers: int = 64,
        history: int = 120,
    ) -> None:
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.min_workers = max(1, min_workers)
        self.hard_max_workers = max(self.min_workers, hard_max_workers)
        self._max_workers = max(self.min_workers, min(max_workers, self.hard_max_workers))
        self._usage_history: deque[dict[str, float]] = deque(maxlen=history)
        self._semaphore: asyncio.Semaphore | None = None
        self._semaphore_limit = self._max_workers
        self._async_lock: asyncio.Lock | None = None
        
        # Intentar cargar psutil
        self._psutil = None
        self._psutil_process = None
        try:
            import psutil
            self._psutil = psutil
            self._psutil_process = psutil.Process(os.getpid())
        except Exception:
            logger.warning("psutil no disponible, usando fallbacks")
    
    @property
    def max_workers(self) -> int:
        """Retornar el presupuesto actual de workers."""
        return self._max_workers
    
    def attach_semaphore(self, semaphore: asyncio.Semaphore) -> None:
        """Adjuntar un semáforo asyncio para control de presupuesto."""
        self._semaphore = semaphore
        self._semaphore_limit = self._max_workers
    
    async def apply_worker_budget(self) -> int:
        """Aplicar el presupuesto actual de workers al semáforo."""
        if self._semaphore is None:
            return self._max_workers
        
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        
        async with self._async_lock:
            desired = self._max_workers
            current = self._semaphore_limit
            
            if desired > current:
                # Liberar tokens
                for _ in range(desired - current):
                    self._semaphore.release()
            elif desired < current:
                # Adquirir tokens
                reduction = current - desired
                for _ in range(reduction):
                    await self._semaphore.acquire()
            
            self._semaphore_limit = desired
            return self._max_workers
    
    def _record_usage(self, usage: dict[str, float]) -> None:
        """Registrar uso de recursos y predecir presupuesto de workers."""
        self._usage_history.append(usage)
        self._predict_worker_budget()
    
    def _predict_worker_budget(self) -> None:
        """Ajustar presupuesto de workers basado en uso reciente."""
        if len(self._usage_history) < 5:
            return
        
        recent_cpu = [e["cpu_percent"] for e in list(self._usage_history)[-5:]]
        recent_mem = [e["memory_percent"] for e in list(self._usage_history)[-5:]]
        
        avg_cpu = statistics.mean(recent_cpu)
        avg_mem = statistics.mean(recent_mem)
        
        new_budget = self._max_workers
        
        # Reducir si recursos altos
        if (self.max_cpu_percent and avg_cpu > self.max_cpu_percent * 0.95) or \
           (self.max_memory_mb and avg_mem > 90.0):
            new_budget = max(self.min_workers, self._max_workers - 1)
        # Aumentar si recursos bajos
        elif avg_cpu < self.max_cpu_percent * 0.6 and avg_mem < 70.0:
            new_budget = min(self.hard_max_workers, self._max_workers + 1)
        
        self._max_workers = max(self.min_workers, min(new_budget, self.hard_max_workers))
    
    def get_resource_usage(self) -> dict[str, float]:
        """Capturar métricas actuales de uso de recursos."""
        timestamp = datetime.utcnow().isoformat()
        cpu_percent = 0.0
        memory_percent = 0.0
        rss_mb = 0.0
        
        if self._psutil:
            try:
                cpu_percent = float(self._psutil.cpu_percent(interval=None))
                virtual_memory = self._psutil.virtual_memory()
                memory_percent = float(virtual_memory.percent)
                if self._psutil_process:
                    rss_mb = float(self._psutil_process.memory_info().rss / (1024 * 1024))
            except Exception:
                cpu_percent = 0.0
        else:
            # Fallback sin psutil
            try:
                load1, _, _ = os.getloadavg()
                cpu_percent = float(min(100.0, load1 * 100))
            except OSError:
                cpu_percent = 0.0
            
            try:
                import resource
                usage_info = resource.getrusage(resource.RUSAGE_SELF)
                rss_mb = float(usage_info.ru_maxrss / 1024)
            except Exception:
                rss_mb = 0.0
        
        usage = {
            "timestamp": timestamp,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "rss_mb": rss_mb,
            "worker_budget": float(self._max_workers),
        }
        
        self._record_usage(usage)
        return usage
    
    def check_memory_exceeded(self, usage: dict[str, float] | None = None) -> tuple[bool, dict[str, float]]:
        """Verificar si se excedió el límite de memoria."""
        usage = usage or self.get_resource_usage()
        exceeded = False
        if self.max_memory_mb is not None:
            exceeded = usage.get("rss_mb", 0.0) > self.max_memory_mb
        return exceeded, usage
    
    def check_cpu_exceeded(self, usage: dict[str, float] | None = None) -> tuple[bool, dict[str, float]]:
        """Verificar si se excedió el límite de CPU."""
        usage = usage or self.get_resource_usage()
        exceeded = False
        if self.max_cpu_percent:
            exceeded = usage.get("cpu_percent", 0.0) > self.max_cpu_percent
        return exceeded, usage
    
    def get_usage_history(self) -> list[dict[str, float]]:
        """Retornar el historial de uso registrado."""
        return list(self._usage_history)


# ============================================================================
# INSTRUMENTACIÓN DE FASES
# ============================================================================

class PhaseInstrumentation:
    """Recolecta telemetría granular para cada fase de orquestación."""
    
    def __init__(
        self,
        phase_id: int,
        name: str,
        items_total: int | None = None,
        snapshot_interval: int = 10,
        resource_limits: ResourceLimits | None = None,
    ) -> None:
        self.phase_id = phase_id
        self.name = name
        self.items_total = items_total or 0
        self.snapshot_interval = max(1, snapshot_interval)
        self.resource_limits = resource_limits
        self.items_processed = 0
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.warnings: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.resource_snapshots: list[dict[str, Any]] = []
        self.latencies: list[float] = []
        self.anomalies: list[dict[str, Any]] = []
    
    def start(self, items_total: int | None = None) -> None:
        """Marcar inicio de ejecución de fase."""
        if items_total is not None:
            self.items_total = items_total
        self.start_time = time.perf_counter()
    
    def increment(self, count: int = 1, latency: float | None = None) -> None:
        """Incrementar contador y opcionalmente registrar latencia."""
        self.items_processed += count
        if latency is not None:
            self.latencies.append(latency)
            self._detect_latency_anomaly(latency)
        if self.resource_limits and self.should_snapshot():
            self.capture_resource_snapshot()
    
    def should_snapshot(self) -> bool:
        """Determinar si se debe capturar un snapshot de recursos."""
        if self.items_total == 0 or self.items_processed == 0:
            return False
        return self.items_processed % self.snapshot_interval == 0
    
    def capture_resource_snapshot(self) -> None:
        """Capturar un snapshot de uso de recursos."""
        if not self.resource_limits:
            return
        snapshot = self.resource_limits.get_resource_usage()
        snapshot["items_processed"] = self.items_processed
        self.resource_snapshots.append(snapshot)
    
    def record_warning(self, category: str, message: str, **extra: Any) -> None:
        """Registrar una advertencia durante ejecución de fase."""
        entry = {
            "category": category,
            "message": message,
            **extra,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.warnings.append(entry)
    
    def record_error(self, category: str, message: str, **extra: Any) -> None:
        """Registrar un error durante ejecución de fase."""
        entry = {
            "category": category,
            "message": message,
            **extra,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.errors.append(entry)
    
    def _detect_latency_anomaly(self, latency: float) -> None:
        """Detectar anomalías de latencia usando umbrales estadísticos."""
        if len(self.latencies) < 5:
            return
        
        mean_latency = statistics.mean(self.latencies)
        std_latency = statistics.pstdev(self.latencies) or 0.0
        threshold = mean_latency + (3 * std_latency)
        
        if std_latency and latency > threshold:
            self.anomalies.append({
                "type": "latency_spike",
                "latency": latency,
                "mean": mean_latency,
                "std": std_latency,
                "timestamp": datetime.utcnow().isoformat(),
            })
    
    def complete(self) -> None:
        """Marcar fin de ejecución de fase."""
        self.end_time = time.perf_counter()
    
    def duration_ms(self) -> float | None:
        """Retornar duración de fase en milisegundos."""
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000.0
    
    def progress(self) -> float | None:
        """Retornar fracción de progreso (0.0 a 1.0)."""
        if not self.items_total:
            return None
        return min(1.0, self.items_processed / float(self.items_total))
    
    def throughput(self) -> float | None:
        """Retornar items procesados por segundo."""
        if self.start_time is None:
            return None
        elapsed = (time.perf_counter() - self.start_time) if self.end_time is None else (self.end_time - self.start_time)
        if not elapsed:
            return None
        return self.items_processed / elapsed
    
    def latency_histogram(self) -> dict[str, float | None]:
        """Retornar percentiles de latencia."""
        if not self.latencies:
            return {"p50": None, "p95": None, "p99": None}
        
        sorted_latencies = sorted(self.latencies)
        
        def percentile(p: float) -> float:
            if not sorted_latencies:
                return 0.0
            k = (len(sorted_latencies) - 1) * (p / 100.0)
            f = int(k)
            c = min(f + 1, len(sorted_latencies) - 1)
            if f == c:
                return sorted_latencies[int(k)]
            d0 = sorted_latencies[f] * (c - k)
            d1 = sorted_latencies[c] * (k - f)
            return d0 + d1
        
        return {
            "p50": percentile(50.0),
            "p95": percentile(95.0),
            "p99": percentile(99.0),
        }
    
    def build_metrics(self) -> dict[str, Any]:
        """Construir diccionario de resumen de métricas."""
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "duration_ms": self.duration_ms(),
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "progress": self.progress(),
            "throughput": self.throughput(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "resource_snapshots": list(self.resource_snapshots),
            "latency_histogram": self.latency_histogram(),
            "anomalies": list(self.anomalies),
        }


# ============================================================================
# TIMEOUT DE FASES
# ============================================================================

class PhaseTimeoutError(RuntimeError):
    """Lanzada cuando una fase excede su timeout."""
    
    def __init__(self, phase_id: int | str, phase_name: str, timeout_s: float) -> None:
        self.phase_id = phase_id
        self.phase_name = phase_name
        self.timeout_s = timeout_s
        super().__init__(f"Phase {phase_id} ({phase_name}) timed out after {timeout_s}s")


async def execute_phase_with_timeout(
    phase_id: int,
    phase_name: str,
    coro: Callable[P, T] | None = None,
    *varargs: P.args,
    handler: Callable[P, T] | None = None,
    args: tuple | None = None,
    timeout_s: float = 300.0,
    **kwargs: P.kwargs,
) -> T:
    """Ejecutar una fase async con timeout y logging comprensivo."""
    target = coro or handler
    if target is None:
        raise ValueError("Either 'coro' or 'handler' must be provided")
    
    call_args = varargs if varargs else (args or ())
    
    start = time.perf_counter()
    logger.info(f"Fase {phase_id} ({phase_name}) iniciada, timeout={timeout_s}s")
    
    try:
        result = await asyncio.wait_for(target(*call_args, **kwargs), timeout=timeout_s)
        elapsed = time.perf_counter() - start
        logger.info(f"Fase {phase_id} completada en {elapsed:.2f}s")
        return result
    
    except asyncio.TimeoutError as exc:
        elapsed = time.perf_counter() - start
        logger.error(f"Fase {phase_id} TIMEOUT después de {elapsed:.2f}s")
        raise PhaseTimeoutError(phase_id, phase_name, timeout_s) from exc
    
    except asyncio.CancelledError:
        elapsed = time.perf_counter() - start
        logger.warning(f"Fase {phase_id} CANCELADA después de {elapsed:.2f}s")
        raise
    
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.error(f"Fase {phase_id} ERROR: {exc} (después de {elapsed:.2f}s)", exc_info=True)
        raise


# ============================================================================
# ORQUESTADOR PRINCIPAL
# ============================================================================

class Orchestrator:
    """Motor de orquestación robusto de 11 fases con soporte de abort y control de recursos."""
    
    # Definición de las 11 fases
    FASES: list[tuple[int, str, str, str]] = [
        (0, "sync", "_load_configuration", "FASE 0 - Validación de Configuración"),
        (1, "sync", "_ingest_document", "FASE 1 - Ingestión de Documento"),
        (2, "async", "_execute_micro_questions_async", "FASE 2 - Micro Preguntas"),
        (3, "async", "_score_micro_results_async", "FASE 3 - Scoring Micro"),
        (4, "async", "_aggregate_dimensions_async", "FASE 4 - Agregación Dimensiones"),
        (5, "async", "_aggregate_policy_areas_async", "FASE 5 - Agregación Áreas"),
        (6, "sync", "_aggregate_clusters", "FASE 6 - Agregación Clústeres"),
        (7, "sync", "_evaluate_macro", "FASE 7 - Evaluación Macro"),
        (8, "async", "_generate_recommendations", "FASE 8 - Recomendaciones"),
        (9, "sync", "_assemble_report", "FASE 9 - Ensamblado de Reporte"),
        (10, "async", "_format_and_export", "FASE 10 - Formateo y Exportación"),
    ]
    
    # Targets de items por fase
    PHASE_ITEM_TARGETS: dict[int, int] = {
        0: 1, 1: 1, 2: 300, 3: 300, 4: 60,
        5: 10, 6: 4, 7: 1, 8: 1, 9: 1, 10: 1,
    }
    
    # Claves de output por fase
    PHASE_OUTPUT_KEYS: dict[int, str] = {
        0: "config", 1: "document", 2: "micro_results",
        3: "scored_results", 4: "dimension_scores",
        5: "policy_area_scores", 6: "cluster_scores",
        7: "macro_result", 8: "recommendations",
        9: "report", 10: "export_payload",
    }
    
    # Argumentos requeridos por fase
    PHASE_ARGUMENT_KEYS: dict[int, list[str]] = {
        1: ["pdf_path", "config"],
        2: ["document", "config"],
        3: ["micro_results", "config"],
        4: ["scored_results", "config"],
        5: ["dimension_scores", "config"],
        6: ["policy_area_scores", "config"],
        7: ["cluster_scores", "config"],
        8: ["macro_result", "config"],
        9: ["recommendations", "config"],
        10: ["report", "config"],
    }
    
    # Timeouts por fase (segundos)
    PHASE_TIMEOUTS: dict[int, float] = {
        0: 60, 1: 120, 2: 600, 3: 300, 4: 180,
        5: 120, 6: 60, 7: 60, 8: 120, 9: 60, 10: 120,
    }
    
    PERCENTAGE_SCALE: int = 100
    
    def __init__(
        self,
        method_executor: Any,
        questionnaire: Any,
        executor_config: Any,
        calibration_orchestrator: Any | None = None,
        resource_limits: ResourceLimits | None = None,
        resource_snapshot_interval: int = 10,
        recommendation_engine_port: Any | None = None,
    ) -> None:
        """Inicializar orquestador con todas las dependencias inyectadas."""
        self.executor = method_executor
        self._canonical_questionnaire = questionnaire
        self._monolith_data = dict(questionnaire.data)
        self.executor_config = executor_config
        self.calibration_orchestrator = calibration_orchestrator
        self.resource_limits = resource_limits or ResourceLimits()
        self.resource_snapshot_interval = max(1, resource_snapshot_interval)
        self.recommendation_engine = recommendation_engine_port
        
        # Inicializar señales y estado
        self.abort_signal = AbortSignal()
        self.phase_results: list[PhaseResult] = []
        self._phase_instrumentation: dict[int, PhaseInstrumentation] = {}
        self._phase_status: dict[int, str] = {
            phase_id: "not_started" for phase_id, *_ in self.FASES
        }
        self._phase_outputs: dict[int, Any] = {}
        self._context: dict[str, Any] = {}
        self._start_time: float | None = None
        
        logger.info("Orchestrator inicializado con 11 fases")
    
    def _ensure_not_aborted(self) -> None:
        """Verificar si la orquestación ha sido abortada y lanzar excepción si es así."""
        if self.abort_signal.is_aborted():
            reason = self.abort_signal.get_reason() or "Unknown reason"
            raise AbortRequested(f"Orchestration aborted: {reason}")
    
    def request_abort(self, reason: str) -> None:
        """Solicitar que la orquestación aborte con una razón específica."""
        self.abort_signal.abort(reason)
    
    def reset_abort(self) -> None:
        """Resetear la señal de abort para permitir nuevas ejecuciones."""
        self.abort_signal.reset()
    
    def _get_phase_timeout(self, phase_id: int) -> float:
        """Obtener timeout para una fase específica."""
        return self.PHASE_TIMEOUTS.get(phase_id, 300.0)
    
    async def process_development_plan_async(
        self,
        pdf_path: str,
        preprocessed_document: Any | None = None
    ) -> list[PhaseResult]:
        """Ejecutar el pipeline completo de 11 fases de forma asíncrona."""
        self.reset_abort()
        self.phase_results = []
        self._phase_instrumentation = {}
        self._phase_outputs = {}
        self._context = {"pdf_path": pdf_path}
        
        if preprocessed_document is not None:
            self._context["preprocessed_override"] = preprocessed_document
        
        self._phase_status = {phase_id: "not_started" for phase_id, *_ in self.FASES}
        self._start_time = time.perf_counter()
        
        # Ejecutar cada fase secuencialmente
        for phase_id, mode, handler_name, phase_label in self.FASES:
            self._ensure_not_aborted()
            
            handler = getattr(self, handler_name)
            instrumentation = PhaseInstrumentation(
                phase_id=phase_id,
                name=phase_label,
                items_total=self.PHASE_ITEM_TARGETS.get(phase_id),
                snapshot_interval=self.resource_snapshot_interval,
                resource_limits=self.resource_limits,
            )
            
            instrumentation.start(items_total=self.PHASE_ITEM_TARGETS.get(phase_id))
            self._phase_instrumentation[phase_id] = instrumentation
            self._phase_status[phase_id] = "running"
            
            # Preparar argumentos
            args = [self._context[key] for key in self.PHASE_ARGUMENT_KEYS.get(phase_id, [])]
            
            success = False
            data: Any = None
            error: Exception | None = None
            
            try:
                if mode == "sync":
                    if phase_id in TIMEOUT_SYNC_PHASES:
                        data = await execute_phase_with_timeout(
                            phase_id, phase_label,
                            asyncio.to_thread, handler, *args,
                            timeout_s=self._get_phase_timeout(phase_id),
                        )
                    else:
                        data = handler(*args)
                else:
                    data = await execute_phase_with_timeout(
                        phase_id, phase_label,
                        handler, *args,
                        timeout_s=self._get_phase_timeout(phase_id),
                    )
                success = True
                
            except PhaseTimeoutError as exc:
                error = exc
                instrumentation.record_error("timeout", str(exc))
                self.request_abort(f"Fase {phase_id} timed out: {exc}")
                
            except AbortRequested as exc:
                error = exc
                instrumentation.record_warning("abort", str(exc))
                
            except Exception as exc:
                logger.exception(f"Fase {phase_label} falló")
                error = exc
                instrumentation.record_error("exception", str(exc))
                self.request_abort(f"Fase {phase_id} falló: {exc}")
            
            finally:
                instrumentation.complete()
            
            aborted = self.abort_signal.is_aborted()
            duration_ms = instrumentation.duration_ms() or 0.0
            
            phase_result = PhaseResult(
                success=success and not aborted,
                phase_id=str(phase_id),
                data=data,
                error=error,
                duration_ms=duration_ms,
                mode=mode,
                aborted=aborted,
            )
            self.phase_results.append(phase_result)
            
            if success and not aborted:
                self._phase_outputs[phase_id] = data
                out_key = self.PHASE_OUTPUT_KEYS.get(phase_id)
                if out_key:
                    self._context[out_key] = data
                self._phase_status[phase_id] = "completed"
            elif aborted:
                self._phase_status[phase_id] = "aborted"
                break
            else:
                self._phase_status[phase_id] = "failed"
                break
        
        return self.phase_results
    
    def get_processing_status(self) -> dict[str, Any]:
        """Obtener estado actual del procesamiento."""
        if self._start_time is None:
            status = "not_started"
            elapsed = 0.0
            completed_flag = False
        else:
            aborted = self.abort_signal.is_aborted()
            status = "aborted" if aborted else "running"
            elapsed = time.perf_counter() - self._start_time
            completed_flag = (
                all(state == "completed" for state in self._phase_status.values())
                and not aborted
            )
        
        completed = sum(1 for state in self._phase_status.values() if state == "completed")
        total = len(self.FASES)
        overall_progress = completed / total if total else 0.0
        
        phase_progress = {
            str(phase_id): instr.progress()
            for phase_id, instr in self._phase_instrumentation.items()
        }
        
        resource_usage = self.resource_limits.get_resource_usage() if self._start_time else {}
        
        return {
            "status": status,
            "overall_progress": overall_progress,
            "phase_progress": phase_progress,
            "elapsed_time_s": elapsed,
            "resource_usage": resource_usage,
            "abort_status": self.abort_signal.is_aborted(),
            "abort_reason": self.abort_signal.get_reason(),
            "completed": completed_flag,
        }
    
    def get_phase_metrics(self) -> dict[str, Any]:
        """Obtener métricas de todas las fases."""
        return {
            str(phase_id): instr.build_metrics()
            for phase_id, instr in self._phase_instrumentation.items()
        }
    
    def health_check(self) -> dict[str, Any]:
        """Verificación de salud del sistema."""
        usage = self.resource_limits.get_resource_usage()
        cpu_headroom = max(0.0, self.resource_limits.max_cpu_percent - usage.get("cpu_percent", 0.0))
        mem_headroom = max(0.0, (self.resource_limits.max_memory_mb or 0.0) - usage.get("rss_mb", 0.0))
        
        score = max(0.0, min(100.0, (cpu_headroom / max(1.0, self.resource_limits.max_cpu_percent)) * 50.0))
        
        if self.resource_limits.max_memory_mb:
            score += max(0.0, min(50.0, (mem_headroom / max(1.0, self.resource_limits.max_memory_mb)) * 50.0))
        
        score = min(100.0, score)
        
        if self.abort_signal.is_aborted():
            score = min(score, 20.0)
        
        return {
            "score": score,
            "resource_usage": usage,
            "abort": self.abort_signal.is_aborted(),
        }
    
    def export_metrics(self) -> dict[str, Any]:
        """Exportar todas las métricas para monitoreo."""
        abort_timestamp = self.abort_signal.get_timestamp()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "phase_metrics": self.get_phase_metrics(),
            "resource_usage": self.resource_limits.get_usage_history(),
            "abort_status": {
                "is_aborted": self.abort_signal.is_aborted(),
                "reason": self.abort_signal.get_reason(),
                "timestamp": abort_timestamp.isoformat() if abort_timestamp else None,
            },
            "phase_status": dict(self._phase_status),
        }
    
    # ========================================================================
    # IMPLEMENTACIÓN DE FASES
    # ========================================================================
    
    def _load_configuration(self) -> dict[str, Any]:
        """FASE 0: Validación de configuración."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[0]
        start = time.perf_counter()
        
        # Normalizar monolito para hash
        monolith = dict(self._monolith_data)
        monolith_hash = hashlib.sha256(
            json.dumps(monolith, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        
        micro_questions = monolith["blocks"].get("micro_questions", [])
        meso_questions = monolith["blocks"].get("meso_questions", [])
        macro_question = monolith["blocks"].get("macro_question", {})
        
        question_total = len(micro_questions) + len(meso_questions) + (1 if macro_question else 0)
        
        if question_total != EXPECTED_QUESTION_COUNT:
            logger.warning(f"Question count mismatch: expected {EXPECTED_QUESTION_COUNT}, got {question_total}")
            instrumentation.record_warning("integrity", f"Conteo de preguntas inesperado: {question_total}")
        
        structure_report = self._validate_contract_structure(monolith, instrumentation)
        
        # Cargar aggregation settings
        from farfan_pipeline.processing.aggregation import AggregationSettings
        aggregation_settings = AggregationSettings.from_monolith(monolith)
        
        duration = time.perf_counter() - start
        instrumentation.increment(latency=duration)
        
        config = {
            "catalog": getattr(self, "catalog", {}),
            "monolith": monolith,
            "monolith_sha256": monolith_hash,
            "micro_questions": micro_questions,
            "meso_questions": meso_questions,
            "macro_question": macro_question,
            "structure_report": structure_report,
            "_aggregation_settings": aggregation_settings,
        }
        
        return config
    
    def _validate_contract_structure(self, monolith: dict[str, Any], instrumentation: PhaseInstrumentation) -> dict[str, Any]:
        """Validar estructura del contrato del cuestionario."""
        micro_questions = monolith["blocks"].get("micro_questions", [])
        base_slots = {q.get("base_slot") for q in micro_questions}
        modalities = {q.get("scoring_modality") for q in micro_questions}
        
        expected_modalities = {"TYPE_A", "TYPE_B", "TYPE_C", "TYPE_D", "TYPE_E", "TYPE_F"}
        
        if len(base_slots) != 30:
            instrumentation.record_error("structure", "Cantidad de slots base inválida", expected=30, found=len(base_slots))
        
        missing_modalities = expected_modalities - modalities
        if missing_modalities:
            instrumentation.record_error("structure", "Modalidades faltantes", missing=sorted(missing_modalities))
        
        slot_area_map: dict[str, str] = {}
        area_cluster_map: dict[str, str] = {}
        
        for question in micro_questions:
            slot = question.get("base_slot")
            area = question.get("policy_area_id")
            cluster = question.get("cluster_id")
            
            if slot and area:
                previous = slot_area_map.setdefault(slot, area)
                if previous != area:
                    instrumentation.record_error("structure", "Asignación de área inconsistente", base_slot=slot)
            
            if area and cluster:
                previous_cluster = area_cluster_map.setdefault(area, cluster)
                if previous_cluster != cluster:
                    instrumentation.record_error("structure", "Área asignada a múltiples clústeres", area=area)
        
        return {
            "base_slots": sorted(base_slots),
            "modalities": sorted(modalities),
            "slot_area_map": slot_area_map,
            "area_cluster_map": area_cluster_map,
        }
    
    def _ingest_document(self, pdf_path: str, config: dict[str, Any]) -> Any:
        """FASE 1: Ingestión de documento usando SPC pipeline."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[1]
        start = time.perf_counter()
        
        document_id = os.path.splitext(os.path.basename(pdf_path))[0] or "doc_1"
        
        # Usar pipeline SPC para ingestion
        try:
            from farfan_pipeline.processing.spc_ingestion import CPPIngestionPipeline
            from farfan_pipeline.core.types import PreprocessedDocument
            
            pipeline = CPPIngestionPipeline()
            canon_package = asyncio.run(pipeline.process(document_path=Path(pdf_path), document_id=document_id))
            
            preprocessed = PreprocessedDocument.ensure(canon_package, document_id=document_id, use_spc_ingestion=True)
            
            # Validar documento no vacío
            if not preprocessed.raw_text or not preprocessed.raw_text.strip():
                raise ValueError("Empty document after ingestion")
            
            # Validar P01-ES v1.0: exactamente 60 chunks
            actual_chunk_count = preprocessed.metadata.get("chunk_count", 0)
            if actual_chunk_count != P01_EXPECTED_CHUNK_COUNT:
                raise ValueError(f"P01 Validation Failed: Expected {P01_EXPECTED_CHUNK_COUNT} chunks, got {actual_chunk_count}")
            
            # Validar metadata en chunks
            for i, chunk in enumerate(preprocessed.chunks):
                if not getattr(chunk, "policy_area_id", None):
                    raise ValueError(f"Chunk {i} missing 'policy_area_id'")
                if not getattr(chunk, "dimension_id", None):
                    raise ValueError(f"Chunk {i} missing 'dimension_id'")
            
            logger.info(f"✅ P01-ES v1.0 validation passed: {actual_chunk_count} chunks")
            
        except Exception as e:
            instrumentation.record_error("ingestion", str(e))
            raise RuntimeError(f"Document ingestion failed: {e}") from e
        
        duration = time.perf_counter() - start
        instrumentation.increment(latency=duration)
        
        return preprocessed
    
    async def _execute_micro_questions_async(self, document: Any, config: dict[str, Any]) -> list[MicroQuestionRun]:
        """FASE 2: Ejecutar micro preguntas con chunk routing."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[2]
        
        micro_questions = config.get("micro_questions", [])
        instrumentation.items_total = len(micro_questions)
        
        # Ordenar preguntas: Dimension -> Policy Area -> Question ID
        ordered_questions = sorted(
            micro_questions,
            key=lambda q: (q.get("dimension_id", "DIM99"), q.get("policy_area_id", "PA99"), q.get("question_id", "Q999"))
        )
        
        # Inicializar chunk router para ejecución chunk-aware
        chunk_routes: dict[int, Any] = {}
        if document.processing_mode == "chunked" and document.chunks:
            try:
                from farfan_pipeline.core.orchestrator.chunk_router import ChunkRouter
                router = ChunkRouter()
                
                for chunk in document.chunks:
                    route = router.route_chunk(chunk)
                    if not route.skip_reason:
                        chunk_routes[chunk.id] = route
                
                logger.info(f"Chunk routing: {len(chunk_routes)} chunks routed from {len(document.chunks)} total")
            except ImportError:
                logger.warning("ChunkRouter not available, using full document mode")
        
        semaphore = asyncio.Semaphore(self.resource_limits.max_workers)
        self.resource_limits.attach_semaphore(semaphore)
        
        # Circuit breakers por base_slot
        circuit_breakers: dict[str, dict[str, Any]] = {
            slot: {"failures": 0, "open": False} for slot in getattr(self, "executors", {})
        }
        
        results: list[MicroQuestionRun] = []
        
        async def process_question(question: dict[str, Any]) -> MicroQuestionRun:
            await self.resource_limits.apply_worker_budget()
            async with semaphore:
                self._ensure_not_aborted()
                
                question_id = question.get("question_id", "")
                question_global = int(question.get("question_global", 0))
                base_slot = question.get("base_slot", "")
                target_pa = question.get("policy_area_id")
                target_dim = question.get("dimension_id")
                
                metadata = {k: question.get(k) for k in ["question_id", "question_global", "base_slot", "dimension_id", "policy_area_id", "cluster_id", "scoring_modality", "expected_elements"]}
                
                # Circuit breaker check
                circuit = circuit_breakers.get(base_slot, {"failures": 0, "open": False})
                if circuit.get("open"):
                    instrumentation.record_warning("circuit_breaker", f"Circuit breaker open for {base_slot}")
                    instrumentation.increment()
                    return MicroQuestionRun(
                        question_id=question_id,
                        question_global=question_global,
                        base_slot=base_slot,
                        metadata=metadata,
                        evidence=None,
                        error="circuit_breaker_open",
                        aborted=False,
                    )
                
                # Resource checks
                usage = self.resource_limits.get_resource_usage()
                mem_exceeded, _ = self.resource_limits.check_memory_exceeded(usage)
                cpu_exceeded, _ = self.resource_limits.check_cpu_exceeded(usage)
                
                if mem_exceeded:
                    instrumentation.record_warning("resource", "Memory limit exceeded")
                if cpu_exceeded:
                    instrumentation.record_warning("resource", "CPU limit exceeded")
                
                start_time = time.perf_counter()
                evidence: Evidence | None = None
                error_message: str | None = None
                
                # Obtener executor class
                executor_class = getattr(self, "executors", {}).get(base_slot)
                
                if not executor_class:
                    error_message = f"Executor not defined for {base_slot}"
                    instrumentation.record_error("executor", error_message)
                else:
                    try:
                        # Instanciar executor
                        executor_instance = executor_class(
                            method_executor=self.executor,
                            signal_registry=getattr(self.executor, "signal_registry", None),
                            config=self.executor_config,
                            questionnaire_provider=getattr(self, "questionnaire_provider", None),
                            calibration_orchestrator=self.calibration_orchestrator,
                            document_id=document.document_id,
                        )
                        
                        # Filtrar chunks por PA y DIM
                        candidate_chunks = [
                            c for c in document.chunks
                            if c.policy_area_id == target_pa and c.dimension_id == target_dim
                        ]
                        
                        # Aplicar chunk routing si disponible
                        if chunk_routes:
                            routed_chunks = []
                            for chunk in candidate_chunks:
                                route = chunk_routes.get(chunk.id)
                                if route:
                                    route_key = route.executor_class
                                    if len(route_key) == 4 and route_key[0] == "D":
                                        route_key = f"{route_key[:2]}-{route_key[2:]}"
                                    if route_key == base_slot:
                                        routed_chunks.append(chunk)
                            candidate_chunks = routed_chunks
                        
                        # Crear documento con scope reducido
                        scoped_document = replace(document, chunks=candidate_chunks)
                        
                        # Ejecutar pregunta
                        evidence = await asyncio.to_thread(
                            executor_instance.execute,
                            scoped_document,
                            self.executor,
                            question_context=question,
                        )
                        
                        circuit["failures"] = 0
                        
                    except Exception as exc:
                        circuit["failures"] += 1
                        error_message = str(exc)
                        instrumentation.record_error("micro_question", error_message, base_slot=base_slot)
                        
                        if circuit["failures"] >= 3:
                            circuit["open"] = True
                            instrumentation.record_warning("circuit_breaker", f"Circuit breaker activated for {base_slot}")
                
                duration = time.perf_counter() - start_time
                instrumentation.increment(latency=duration)
                
                if instrumentation.items_processed % 10 == 0:
                    logger.info(f"Progress: {instrumentation.items_processed}/{instrumentation.items_total}")
                
                return MicroQuestionRun(
                    question_id=question_id,
                    question_global=question_global,
                    base_slot=base_slot,
                    metadata=metadata,
                    evidence=evidence,
                    error=error_message,
                    duration_ms=duration * 1000.0,
                    aborted=self.abort_signal.is_aborted(),
                )
        
        tasks = [asyncio.create_task(process_question(q)) for q in ordered_questions]
        
        try:
            for task in asyncio.as_completed(tasks):
                result = await task
                results.append(result)
                if self.abort_signal.is_aborted():
                    raise AbortRequested(self.abort_signal.get_reason() or "Abort requested")
        except AbortRequested:
            for task in tasks:
                task.cancel()
            raise
        
        return results
    
    async def _score_micro_results_async(self, micro_results: list[MicroQuestionRun], config: dict[str, Any]) -> list[ScoredMicroQuestion]:
        """FASE 3: Scoring de micro resultados usando MicroQuestionScorer."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[3]
        instrumentation.items_total = len(micro_results)
        
        # Importar scorer desde análisis
        from farfan_pipeline.analysis.scoring import MicroQuestionScorer, ScoringModality, Evidence as ScoringEvidence
        
        scorer = MicroQuestionScorer()
        results: list[ScoredMicroQuestion] = []
        
        semaphore = asyncio.Semaphore(self.resource_limits.max_workers)
        self.resource_limits.attach_semaphore(semaphore)
        
        async def score_item(item: MicroQuestionRun) -> ScoredMicroQuestion:
            async with semaphore:
                await self.resource_limits.apply_worker_budget()
                self._ensure_not_aborted()
                start = time.perf_counter()
                
                modality_value = item.metadata.get("scoring_modality", "TYPE_A")
                try:
                    modality = ScoringModality(modality_value)
                except Exception:
                    modality = ScoringModality.TYPE_A
                
                # Si no hay evidencia, retornar score nulo
                if item.error or not item.evidence:
                    instrumentation.record_warning("scoring", "Missing evidence", question_id=item.question_id)
                    instrumentation.increment(latency=time.perf_counter() - start)
                    return ScoredMicroQuestion(
                        question_id=item.question_id,
                        question_global=item.question_global,
                        base_slot=item.base_slot,
                        score=None,
                        normalized_score=None,
                        quality_level=None,
                        evidence=item.evidence,
                        metadata=item.metadata,
                        error=item.error or "missing_evidence",
                    )
                
                # Extraer elementos de evidencia
                if isinstance(item.evidence, dict):
                    elements_found = item.evidence.get("elements", [])
                    raw_results = item.evidence.get("raw_results", {})
                else:
                    elements_found = getattr(item.evidence, "elements", [])
                    raw_results = getattr(item.evidence, "raw_results", {})
                
                # Construir scoring evidence
                scoring_evidence = ScoringEvidence(
                    elements_found=elements_found,
                    confidence_scores=raw_results.get("confidence_scores", []),
                    semantic_similarity=raw_results.get("semantic_similarity"),
                    pattern_matches=raw_results.get("pattern_matches", {}),
                    metadata=raw_results,
                )
                
                try:
                    # Aplicar scoring
                    scored = await asyncio.to_thread(
                        scorer.apply_scoring_modality,
                        item.question_id,
                        item.question_global,
                        modality,
                        scoring_evidence,
                    )
                    
                    duration = time.perf_counter() - start
                    instrumentation.increment(latency=duration)
                    
                    return ScoredMicroQuestion(
                        question_id=scored.question_id,
                        question_global=scored.question_global,
                        base_slot=item.base_slot,
                        score=scored.raw_score,
                        normalized_score=scored.normalized_score,
                        quality_level=scored.quality_level.value,
                        evidence=item.evidence,
                        scoring_details=scored.scoring_details,
                        metadata=item.metadata,
                    )
                    
                except Exception as exc:
                    instrumentation.record_error("scoring", str(exc), question_id=item.question_id)
                    duration = time.perf_counter() - start
                    instrumentation.increment(latency=duration)
                    
                    return ScoredMicroQuestion(
                        question_id=item.question_id,
                        question_global=item.question_global,
                        base_slot=item.base_slot,
                        score=None,
                        normalized_score=None,
                        quality_level=None,
                        evidence=item.evidence,
                        metadata=item.metadata,
                        error=str(exc),
                    )
        
        tasks = [asyncio.create_task(score_item(item)) for item in micro_results]
        
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            if self.abort_signal.is_aborted():
                raise AbortRequested(self.abort_signal.get_reason() or "Abort requested")
        
        return results
    
    async def _aggregate_dimensions_async(self, scored_results: list[ScoredMicroQuestion], config: dict[str, Any]) -> list[Any]:
        """FASE 4: Agregación de dimensiones usando DimensionAggregator."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[4]
        
        from farfan_pipeline.processing.aggregation import DimensionAggregator, validate_scored_results, group_by
        
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith for dimension aggregation")
            return []
        
        aggregation_settings = config.get("_aggregation_settings")
        aggregator = DimensionAggregator(monolith, abort_on_insufficient=False, aggregation_settings=aggregation_settings)
        
        # Convertir scored results a payloads
        scored_payloads = []
        for item in scored_results:
            if item.score is None:
                continue
            
            metadata = item.metadata or {}
            policy_area = metadata.get("policy_area_id") or metadata.get("policy_area") or ""
            dimension = metadata.get("dimension_id") or metadata.get("dimension") or ""
            
            evidence_payload = asdict(item.evidence) if is_dataclass(item.evidence) else (item.evidence if isinstance(item.evidence, dict) else {})
            raw_results = item.scoring_details if isinstance(item.scoring_details, dict) else {}
            
            scored_payloads.append({
                "question_global": item.question_global,
                "base_slot": item.base_slot,
                "policy_area": str(policy_area),
                "dimension": str(dimension),
                "score": float(item.score),
                "quality_level": str(item.quality_level or "INSUFICIENTE"),
                "evidence": evidence_payload,
                "raw_results": raw_results,
            })
        
        if not scored_payloads:
            instrumentation.items_total = 0
            return []
        
        # Validar y agrupar
        validated_results = validate_scored_results(scored_payloads)
        group_by_keys = aggregator.dimension_group_by_keys
        key_func = lambda result: tuple(getattr(result, key, None) for key in group_by_keys)
        grouped_results = group_by(validated_results, key_func)
        
        instrumentation.items_total = len(grouped_results)
        dimension_scores = []
        
        for group_key, items in grouped_results.items():
            self._ensure_not_aborted()
            await asyncio.sleep(0)
            start = time.perf_counter()
            
            group_by_values = dict(zip(group_by_keys, group_key, strict=False))
            
            try:
                dim_score = aggregator.aggregate_dimension(scored_results=items, group_by_values=group_by_values)
                dimension_scores.append(dim_score)
            except Exception as exc:
                logger.error(f"Failed to aggregate dimension {group_by_values}: {exc}")
            
            instrumentation.increment(latency=time.perf_counter() - start)
        
        return dimension_scores
    
    async def _aggregate_policy_areas_async(self, dimension_scores: list[Any], config: dict[str, Any]) -> list[Any]:
        """FASE 5: Agregación de policy areas usando AreaPolicyAggregator."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[5]
        
        from farfan_pipeline.processing.aggregation import AreaPolicyAggregator, group_by
        
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith for area aggregation")
            return []
        
        aggregation_settings = config.get("_aggregation_settings")
        aggregator = AreaPolicyAggregator(monolith, abort_on_insufficient=False, aggregation_settings=aggregation_settings)
        
        # Agrupar por policy area
        group_by_keys = aggregator.area_group_by_keys
        key_func = lambda score: tuple(getattr(score, key, None) for key in group_by_keys)
        grouped_scores = group_by(dimension_scores, key_func)
        
        instrumentation.items_total = len(grouped_scores)
        area_scores = []
        
        for group_key, scores in grouped_scores.items():
            self._ensure_not_aborted()
            await asyncio.sleep(0)
            start = time.perf_counter()
            
            group_by_values = dict(zip(group_by_keys, group_key, strict=False))
            
            try:
                area_score = aggregator.aggregate_area(dimension_scores=scores, group_by_values=group_by_values)
                area_scores.append(area_score)
            except Exception as exc:
                logger.error(f"Failed to aggregate policy area {group_by_values}: {exc}")
            
            instrumentation.increment(latency=time.perf_counter() - start)
        
        return area_scores
    
    def _aggregate_clusters(self, policy_area_scores: list[Any], config: dict[str, Any]) -> list[Any]:
        """FASE 6: Agregación de clusters usando ClusterAggregator."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[6]
        
        from farfan_pipeline.processing.aggregation import ClusterAggregator, group_by
        
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith for cluster aggregation")
            return []
        
        aggregation_settings = config.get("_aggregation_settings")
        aggregator = ClusterAggregator(monolith, abort_on_insufficient=False, aggregation_settings=aggregation_settings)
        
        # Mapear areas a clusters
        clusters = monolith["blocks"]["niveles_abstraccion"]["clusters"]
        area_to_cluster = {}
        for cluster in clusters:
            cluster_id = cluster.get("cluster_id")
            for area_id in cluster.get("policy_area_ids", []):
                if cluster_id and area_id:
                    area_to_cluster[area_id] = cluster_id
        
        # Enriquecer scores con cluster_id
        enriched_scores = []
        for score in policy_area_scores:
            cluster_id = area_to_cluster.get(score.area_id)
            if not cluster_id:
                logger.warning(f"Area {score.area_id} not mapped to cluster")
                continue
            score.cluster_id = cluster_id
            enriched_scores.append(score)
        
        # Agrupar por cluster
        group_by_keys = aggregator.cluster_group_by_keys
        key_func = lambda area_score: tuple(getattr(area_score, key, None) for key in group_by_keys)
        grouped_scores = group_by(enriched_scores, key_func)
        
        instrumentation.items_total = len(grouped_scores)
        cluster_scores = []
        
        for group_key, scores in grouped_scores.items():
            self._ensure_not_aborted()
            start = time.perf_counter()
            
            group_by_values = dict(zip(group_by_keys, group_key, strict=False))
            
            try:
                cluster_score = aggregator.aggregate_cluster(area_scores=scores, group_by_values=group_by_values)
                cluster_scores.append(cluster_score)
            except Exception as exc:
                logger.error(f"Failed to aggregate cluster {group_by_values}: {exc}")
            
            instrumentation.increment(latency=time.perf_counter() - start)
        
        return cluster_scores
    
    def _evaluate_macro(self, cluster_scores: list[Any], config: dict[str, Any]) -> dict[str, Any]:
        """FASE 7: Evaluación macro usando MacroAggregator."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[7]
        start = time.perf_counter()
        
        from farfan_pipeline.processing.aggregation import MacroAggregator, MacroScore
        
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith for macro evaluation")
            return {"macro_score": None, "macro_score_normalized": 0.0, "cluster_scores": cluster_scores}
        
        aggregation_settings = config.get("_aggregation_settings")
        aggregator = MacroAggregator(monolith, abort_on_insufficient=False, aggregation_settings=aggregation_settings)
        
        # Extraer area_scores y dimension_scores
        area_scores = []
        dimension_scores = []
        
        for cluster in cluster_scores:
            area_scores.extend(cluster.area_scores)
            for area in cluster.area_scores:
                dimension_scores.extend(area.dimension_scores)
        
        # Eliminar duplicados
        seen_areas = set()
        unique_areas = []
        for area in area_scores:
            if area.area_id not in seen_areas:
                seen_areas.add(area.area_id)
                unique_areas.append(area)
        
        seen_dims = set()
        unique_dims = []
        for dim in dimension_scores:
            key = (dim.dimension_id, dim.area_id)
            if key not in seen_dims:
                seen_dims.add(key)
                unique_dims.append(dim)
        
        # Evaluar macro
        try:
            macro_score = aggregator.evaluate_macro(
                cluster_scores=cluster_scores,
                area_scores=unique_areas,
                dimension_scores=unique_dims,
            )
        except Exception as e:
            logger.error(f"Macro evaluation failed: {e}")
            macro_score = MacroScore(
                score=0.0,
                quality_level="INSUFICIENTE",
                cross_cutting_coherence=0.0,
                systemic_gaps=[],
                strategic_alignment=0.0,
                cluster_scores=cluster_scores,
                validation_passed=False,
                validation_details={"error": str(e), "type": "exception"},
            )
        
        instrumentation.increment(latency=time.perf_counter() - start)
        
        macro_score_normalized = float(macro_score.score) if isinstance(macro_score, MacroScore) else float(macro_score)
        
        return {
            "macro_score": macro_score,
            "macro_score_normalized": macro_score_normalized,
            "cluster_scores": cluster_scores,
            "cross_cutting_coherence": macro_score.cross_cutting_coherence,
            "systemic_gaps": macro_score.systemic_gaps,
            "strategic_alignment": macro_score.strategic_alignment,
            "quality_band": macro_score.quality_level,
        }
    
    async def _generate_recommendations(self, macro_result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """FASE 8: Generación de recomendaciones en 3 niveles."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[8]
        start = time.perf_counter()
        
        await asyncio.sleep(0)
        
        if self.recommendation_engine is None:
            logger.warning("RecommendationEngine not available")
            recommendations = {
                "MICRO": {"level": "MICRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MESO": {"level": "MESO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MACRO": {"level": "MACRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "macro_score": macro_result.get("macro_score"),
            }
            instrumentation.increment(latency=time.perf_counter() - start)
            return recommendations
        
        try:
            # Extraer micro scores (PA-DIM)
            micro_scores: dict[str, float] = {}
            scored_results = self._context.get("scored_results", [])
            
            pa_dim_groups: dict[str, list[float]] = {}
            for result in scored_results:
                if hasattr(result, "metadata") and result.metadata:
                    pa_id = result.metadata.get("policy_area_id")
                    dim_id = result.metadata.get("dimension_id")
                    score = result.normalized_score
                    
                    if pa_id and dim_id and score is not None:
                        key = f"{pa_id}-{dim_id}"
                        if key not in pa_dim_groups:
                            pa_dim_groups[key] = []
                        pa_dim_groups[key].append(score)
            
            for key, scores in pa_dim_groups.items():
                if scores:
                    micro_scores[key] = sum(scores) / len(scores)
            
            # Extraer cluster data
            cluster_data: dict[str, Any] = {}
            cluster_scores = self._context.get("cluster_scores", [])
            
            for cluster in cluster_scores:
                cluster_id = cluster.get("cluster_id")
                cluster_score = cluster.get("score")
                areas = cluster.get("areas", [])
                
                if cluster_id and cluster_score is not None:
                    valid_area_scores = [(area, area.get("score")) for area in areas if area.get("score") is not None]
                    area_values = [score for _, score in valid_area_scores]
                    variance = statistics.variance(area_values) if len(area_values) > 1 else 0.0
                    
                    weakest_area = min(valid_area_scores, key=lambda item: item[1]) if valid_area_scores else None
                    weak_pa = weakest_area[0].get("area_id") if weakest_area else None
                    
                    cluster_data[cluster_id] = {
                        "score": cluster_score * self.PERCENTAGE_SCALE,
                        "variance": variance,
                        "weak_pa": weak_pa,
                    }
            
            # Extraer macro data
            macro_score_normalized = macro_result.get("macro_score_normalized")
            
            macro_band = "INSUFICIENTE"
            if macro_score_normalized is not None:
                scaled = float(macro_score_normalized) * self.PERCENTAGE_SCALE
                if scaled >= 75:
                    macro_band = "SATISFACTORIO"
                elif scaled >= 55:
                    macro_band = "ACEPTABLE"
                elif scaled >= 35:
                    macro_band = "DEFICIENTE"
            
            clusters_below_target = []
            for cluster in cluster_scores:
                if cluster.get("score", 0) * self.PERCENTAGE_SCALE < 55:
                    clusters_below_target.append(cluster.get("cluster_id"))
            
            cluster_score_values = [c.get("score") for c in cluster_scores if c.get("score") is not None]
            overall_variance = statistics.variance(cluster_score_values) if len(cluster_score_values) > 1 else 0.0
            
            variance_alert = "BAJA"
            if overall_variance >= 0.18:
                variance_alert = "ALTA"
            elif overall_variance >= 0.08:
                variance_alert = "MODERADA"
            
            sorted_micro = sorted(micro_scores.items(), key=lambda x: x[1])
            priority_micro_gaps = [k for k, v in sorted_micro[:5] if v < 0.55]
            
            macro_data = {
                "macro_band": macro_band,
                "clusters_below_target": clusters_below_target,
                "variance_alert": variance_alert,
                "priority_micro_gaps": priority_micro_gaps,
                "macro_score_percentage": float(macro_score_normalized) * self.PERCENTAGE_SCALE if macro_score_normalized else None,
            }
            
            # Generar recomendaciones
            context = {
                "generated_at": datetime.utcnow().isoformat(),
                "macro_score": macro_result.get("macro_score"),
            }
            
            recommendation_sets = self.recommendation_engine.generate_all_recommendations(
                micro_scores=micro_scores,
                cluster_data=cluster_data,
                macro_data=macro_data,
                context=context,
            )
            
            recommendations = {level: rec_set.to_dict() for level, rec_set in recommendation_sets.items()}
            recommendations["macro_score"] = macro_result.get("macro_score")
            recommendations["macro_score_normalized"] = macro_score_normalized
            
            logger.info(f"Generated recommendations: MICRO={len(recommendation_sets['MICRO'].recommendations)}, MESO={len(recommendation_sets['MESO'].recommendations)}, MACRO={len(recommendation_sets['MACRO'].recommendations)}")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            recommendations = {
                "MICRO": {"level": "MICRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MESO": {"level": "MESO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MACRO": {"level": "MACRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "macro_score": macro_result.get("macro_score"),
                "error": str(e),
            }
        
        instrumentation.increment(latency=time.perf_counter() - start)
        return recommendations
    
    def _assemble_report(self, recommendations: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """FASE 9: Ensamblado de reporte."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[9]
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "recommendations": recommendations,
            "metadata": {
                "monolith_sha256": config.get("monolith_sha256"),
            },
        }
        
        instrumentation.increment()
        return report
    
    async def _format_and_export(self, report: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """FASE 10: Formateo y exportación."""
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[10]
        
        await asyncio.sleep(0)
        
        export_payload = {
            "report": report,
            "phase_metrics": self.get_phase_metrics(),
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        instrumentation.increment()
        return export_payload
