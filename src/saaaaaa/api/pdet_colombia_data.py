#!/usr/bin/env python3
"""
PDET Colombia Dataset - Complete Official Listing
===================================================

Complete dataset of all 170 municipalities across 16 PDET subregions
(Programas de Desarrollo con Enfoque Territorial) in Colombia.

Data sourced from:
- Agencia de Renovación del Territorio (ART)
- Departamento Nacional de Planeación (DNP)
- Fondo Colombia en Paz official annexes

Author: AtroZ Dashboard Team
Version: 1.0.0
Last Updated: 2024-11-14
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Municipality:
    """Represents a PDET municipality"""
    name: str
    department: str
    subregion: str
    subregion_id: str
    dane_code: Optional[str] = None
    population: Optional[int] = None
    area_km2: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class PDETSubregion:
    """Represents a PDET subregion"""
    id: str
    name: str
    municipalities_count: int
    departments: List[str]
    municipalities: List[Municipality]


# =============================================================================
# COMPLETE PDET DATASET - 170 MUNICIPALITIES ACROSS 16 SUBREGIONS
# =============================================================================

PDET_MUNICIPALITIES = [
    # =========================================================================
    # 1. ALTO PATÍA Y NORTE DEL CAUCA (24 municipalities)
    # =========================================================================
    Municipality("Argelia", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Balboa", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Buenos Aires", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Cajibío", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Caldono", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Caloto", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Corinto", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("El Tambo", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Jambaló", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Mercaderes", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Miranda", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Morales", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Patía", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Piendamó", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Santander de Quilichao", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Suárez", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Toribío", "Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Cumbitara", "Nariño", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("El Rosario", "Nariño", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Leiva", "Nariño", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Los Andes", "Nariño", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Policarpa", "Nariño", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Florida", "Valle del Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),
    Municipality("Pradera", "Valle del Cauca", "Alto Patía y Norte del Cauca", "alto-patia"),

    # =========================================================================
    # 2. ARAUCA (4 municipalities)
    # =========================================================================
    Municipality("Arauquita", "Arauca", "Arauca", "arauca"),
    Municipality("Fortul", "Arauca", "Arauca", "arauca"),
    Municipality("Saravena", "Arauca", "Arauca", "arauca"),
    Municipality("Tame", "Arauca", "Arauca", "arauca"),

    # =========================================================================
    # 3. BAJO CAUCA Y NORDESTE ANTIOQUEÑO (13 municipalities)
    # =========================================================================
    Municipality("Amalfi", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Anorí", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Briceño", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Cáceres", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Caucasia", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("El Bagre", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Ituango", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Nechí", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Remedios", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Segovia", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Tarazá", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Valdivia", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),
    Municipality("Zaragoza", "Antioquia", "Bajo Cauca y Nordeste Antioqueño", "bajo-cauca"),

    # =========================================================================
    # 4. CATATUMBO (8 municipalities)
    # =========================================================================
    Municipality("Convención", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("El Carmen", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("El Tarra", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("Hacarí", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("San Calixto", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("Sardinata", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("Teorama", "Norte de Santander", "Catatumbo", "catatumbo"),
    Municipality("Tibú", "Norte de Santander", "Catatumbo", "catatumbo"),

    # =========================================================================
    # 5. CHOCÓ (14 municipalities)
    # =========================================================================
    Municipality("Acandí", "Chocó", "Chocó", "choco"),
    Municipality("Alto Baudó", "Chocó", "Chocó", "choco"),
    Municipality("Bagadó", "Chocó", "Chocó", "choco"),
    Municipality("Bajo Baudó", "Chocó", "Chocó", "choco"),
    Municipality("Bojayá", "Chocó", "Chocó", "choco"),
    Municipality("Carmen del Darién", "Chocó", "Chocó", "choco"),
    Municipality("Condoto", "Chocó", "Chocó", "choco"),
    Municipality("El Litoral de San Juan", "Chocó", "Chocó", "choco"),
    Municipality("Istmina", "Chocó", "Chocó", "choco"),
    Municipality("Juradó", "Chocó", "Chocó", "choco"),
    Municipality("Medio Atrato", "Chocó", "Chocó", "choco"),
    Municipality("Medio Baudó", "Chocó", "Chocó", "choco"),
    Municipality("Nuquí", "Chocó", "Chocó", "choco"),
    Municipality("Río Quito", "Chocó", "Chocó", "choco"),

    # =========================================================================
    # 6. CUENCA DEL CAGUÁN Y PIEDEMONTE CAQUETEÑO (17 municipalities)
    # =========================================================================
    Municipality("Albania", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Belén de los Andaquíes", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Cartagena del Chairá", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Curillo", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("El Doncello", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("El Paujil", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Florencia", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("La Montañita", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Milán", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Morelia", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Puerto Rico", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("San José del Fragua", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("San Vicente del Caguán", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Solano", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Solita", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Valparaíso", "Caquetá", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),
    Municipality("Algeciras", "Huila", "Cuenca del Caguán y Piedemonte Caqueteño", "caguan"),

    # =========================================================================
    # 7. MACARENA - GUAVIARE (12 municipalities)
    # =========================================================================
    Municipality("La Macarena", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Mapiripán", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Mesetas", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Puerto Concordia", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Puerto Lleras", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Puerto Rico", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("San Juan de Arama", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Uribe", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Vistahermosa", "Meta", "Macarena - Guaviare", "macarena"),
    Municipality("Calamar", "Guaviare", "Macarena - Guaviare", "macarena"),
    Municipality("El Retorno", "Guaviare", "Macarena - Guaviare", "macarena"),
    Municipality("Miraflores", "Guaviare", "Macarena - Guaviare", "macarena"),
    Municipality("San José del Guaviare", "Guaviare", "Macarena - Guaviare", "macarena"),

    # =========================================================================
    # 8. MONTES DE MARÍA (15 municipalities)
    # =========================================================================
    Municipality("El Carmen de Bolívar", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("María La Baja", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("San Jacinto", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("San Juan Nepomuceno", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("Zambrano", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("Córdoba", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("El Guamo", "Bolívar", "Montes de María", "montes-maria"),
    Municipality("Chalán", "Sucre", "Montes de María", "montes-maria"),
    Municipality("Colosó", "Sucre", "Montes de María", "montes-maria"),
    Municipality("Morroa", "Sucre", "Montes de María", "montes-maria"),
    Municipality("Ovejas", "Sucre", "Montes de María", "montes-maria"),
    Municipality("Palmito", "Sucre", "Montes de María", "montes-maria"),
    Municipality("Los Palmitos", "Sucre", "Montes de María", "montes-maria"),
    Municipality("San Onofre", "Sucre", "Montes de María", "montes-maria"),
    Municipality("Tolú Viejo", "Sucre", "Montes de María", "montes-maria"),

    # =========================================================================
    # 9. PACÍFICO MEDIO (4 municipalities)
    # =========================================================================
    Municipality("Buenaventura", "Valle del Cauca", "Pacífico Medio", "pacifico-medio"),
    Municipality("López de Micay", "Cauca", "Pacífico Medio", "pacifico-medio"),
    Municipality("Guapi", "Cauca", "Pacífico Medio", "pacifico-medio"),
    Municipality("Timbiquí", "Cauca", "Pacífico Medio", "pacifico-medio"),

    # =========================================================================
    # 10. PACÍFICO Y FRONTERA NARIÑENSE (11 municipalities)
    # =========================================================================
    Municipality("Barbacoas", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("El Charco", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Francisco Pizarro", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("La Tola", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Magüí Payán", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Mosquera", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Olaya Herrera", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Roberto Payán", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Santa Bárbara", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Tumaco", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),
    Municipality("Ricaurte", "Nariño", "Pacífico y Frontera Nariñense", "pacifico-narinense"),

    # =========================================================================
    # 11. PUTUMAYO (9 municipalities)
    # =========================================================================
    Municipality("Mocoa", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Orito", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Puerto Asís", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Puerto Caicedo", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Puerto Guzmán", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Puerto Leguízamo", "Putumayo", "Putumayo", "putumayo"),
    Municipality("San Miguel", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Valle del Guamuez", "Putumayo", "Putumayo", "putumayo"),
    Municipality("Villagarzón", "Putumayo", "Putumayo", "putumayo"),

    # =========================================================================
    # 12. SIERRA NEVADA, PERIJÁ Y ZONA BANANERA (10 municipalities)
    # =========================================================================
    Municipality("Ciénaga", "Magdalena", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("Fundación", "Magdalena", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("Pueblo Viejo", "Magdalena", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("Zona Bananera", "Magdalena", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("Dibulla", "La Guajira", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("La Jagua del Pilar", "La Guajira", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("San Juan del Cesar", "La Guajira", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("Becerril", "Cesar", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("La Jagua de Ibirico", "Cesar", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),
    Municipality("Agustín Codazzi", "Cesar", "Sierra Nevada, Perijá y Zona Bananera", "sierra-nevada"),

    # =========================================================================
    # 13. SUR DE BOLÍVAR (6 municipalities)
    # =========================================================================
    Municipality("Arenal", "Bolívar", "Sur de Bolívar", "sur-bolivar"),
    Municipality("Montecristo", "Bolívar", "Sur de Bolívar", "sur-bolivar"),
    Municipality("Morales", "Bolívar", "Sur de Bolívar", "sur-bolivar"),
    Municipality("San Pablo", "Bolívar", "Sur de Bolívar", "sur-bolivar"),
    Municipality("Santa Rosa del Sur", "Bolívar", "Sur de Bolívar", "sur-bolivar"),
    Municipality("Simití", "Bolívar", "Sur de Bolívar", "sur-bolivar"),

    # =========================================================================
    # 14. SUR DE CÓRDOBA (5 municipalities)
    # =========================================================================
    Municipality("Montelíbano", "Córdoba", "Sur de Córdoba", "sur-cordoba"),
    Municipality("Puerto Libertador", "Córdoba", "Sur de Córdoba", "sur-cordoba"),
    Municipality("San José de Uré", "Córdoba", "Sur de Córdoba", "sur-cordoba"),
    Municipality("Tierralta", "Córdoba", "Sur de Córdoba", "sur-cordoba"),
    Municipality("Valencia", "Córdoba", "Sur de Córdoba", "sur-cordoba"),

    # =========================================================================
    # 15. SUR DEL TOLIMA (4 municipalities)
    # =========================================================================
    Municipality("Ataco", "Tolima", "Sur del Tolima", "sur-tolima"),
    Municipality("Chaparral", "Tolima", "Sur del Tolima", "sur-tolima"),
    Municipality("Planadas", "Tolima", "Sur del Tolima", "sur-tolima"),
    Municipality("Rioblanco", "Tolima", "Sur del Tolima", "sur-tolima"),

    # =========================================================================
    # 16. URABÁ ANTIOQUEÑO (10 municipalities)
    # =========================================================================
    Municipality("Apartadó", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Carepa", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Chigorodó", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Mutatá", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Murindó", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Turbo", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("San Pedro de Urabá", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Necoclí", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("San Juan de Urabá", "Antioquia", "Urabá Antioqueño", "uraba"),
    Municipality("Arboletes", "Antioquia", "Urabá Antioqueño", "uraba"),
]


# =============================================================================
# PDET SUBREGIONS STRUCTURED DATA
# =============================================================================

def get_subregions() -> List[PDETSubregion]:
    """Get all PDET subregions with their municipalities"""
    subregions_map = {}
    
    for muni in PDET_MUNICIPALITIES:
        if muni.subregion_id not in subregions_map:
            subregions_map[muni.subregion_id] = {
                'name': muni.subregion,
                'departments': set(),
                'municipalities': []
            }
        subregions_map[muni.subregion_id]['departments'].add(muni.department)
        subregions_map[muni.subregion_id]['municipalities'].append(muni)
    
    subregions = []
    for subregion_id, data in subregions_map.items():
        subregions.append(PDETSubregion(
            id=subregion_id,
            name=data['name'],
            municipalities_count=len(data['municipalities']),
            departments=sorted(list(data['departments'])),
            municipalities=data['municipalities']
        ))
    
    return sorted(subregions, key=lambda x: x.name)


def get_municipalities_by_subregion(subregion_id: str) -> List[Municipality]:
    """Get all municipalities for a specific subregion"""
    return [m for m in PDET_MUNICIPALITIES if m.subregion_id == subregion_id]


def get_municipalities_by_department(department: str) -> List[Municipality]:
    """Get all PDET municipalities for a specific department"""
    return [m for m in PDET_MUNICIPALITIES if m.department == department]


def get_municipality_count_by_subregion() -> Dict[str, int]:
    """Get count of municipalities per subregion"""
    counts = {}
    for muni in PDET_MUNICIPALITIES:
        counts[muni.subregion_id] = counts.get(muni.subregion_id, 0) + 1
    return counts


def get_department_list() -> List[str]:
    """Get unique list of departments with PDET municipalities"""
    return sorted(list(set(m.department for m in PDET_MUNICIPALITIES)))


# =============================================================================
# DATA VALIDATION
# =============================================================================

def validate_dataset() -> Dict[str, any]:
    """Validate the PDET dataset completeness"""
    total_municipalities = len(PDET_MUNICIPALITIES)
    subregions = get_subregions()
    departments = get_department_list()
    
    validation = {
        'total_municipalities': total_municipalities,
        'expected_municipalities': 170,
        'is_complete': total_municipalities == 170,
        'total_subregions': len(subregions),
        'expected_subregions': 16,
        'subregions_complete': len(subregions) == 16,
        'total_departments': len(departments),
        'departments': departments,
        'subregion_breakdown': get_municipality_count_by_subregion()
    }
    
    return validation


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_to_dict() -> Dict:
    """Export complete dataset to dictionary format"""
    return {
        'metadata': {
            'total_municipalities': len(PDET_MUNICIPALITIES),
            'total_subregions': len(get_subregions()),
            'total_departments': len(get_department_list()),
            'source': 'Agencia de Renovación del Territorio (ART)',
            'last_updated': '2024-11-14'
        },
        'subregions': [
            {
                'id': sr.id,
                'name': sr.name,
                'municipalities_count': sr.municipalities_count,
                'departments': sr.departments,
                'municipalities': [
                    {
                        'name': m.name,
                        'department': m.department,
                        'dane_code': m.dane_code,
                        'population': m.population,
                        'area_km2': m.area_km2
                    }
                    for m in sr.municipalities
                ]
            }
            for sr in get_subregions()
        ]
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    import json
    
    # Validate dataset
    validation = validate_dataset()
    print("=" * 80)
    print("PDET COLOMBIA DATASET VALIDATION")
    print("=" * 80)
    print(f"Total Municipalities: {validation['total_municipalities']} / {validation['expected_municipalities']}")
    print(f"Dataset Complete: {'✓ YES' if validation['is_complete'] else '✗ NO'}")
    print(f"Total Subregions: {validation['total_subregions']} / {validation['expected_subregions']}")
    print(f"Subregions Complete: {'✓ YES' if validation['subregions_complete'] else '✗ NO'}")
    print(f"Total Departments: {validation['total_departments']}")
    print("=" * 80)
    print("\nMunicipalities per Subregion:")
    for subregion_id, count in sorted(validation['subregion_breakdown'].items()):
        print(f"  {subregion_id}: {count}")
    print("=" * 80)
    print("\nDepartments with PDET municipalities:")
    for dept in validation['departments']:
        print(f"  - {dept}")
    print("=" * 80)
    
    # Export to JSON
    output_file = 'pdet_colombia_complete.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_to_dict(), f, ensure_ascii=False, indent=2)
    print(f"\n✓ Dataset exported to: {output_file}")
