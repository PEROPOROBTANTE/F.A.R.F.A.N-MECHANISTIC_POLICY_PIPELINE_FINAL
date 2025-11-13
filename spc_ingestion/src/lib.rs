// Canon Policy Package Ingestion - Rust Core
//
// Performance-critical operations:
// - BLAKE3 hashing
// - Unicode normalization
// - Arrow IPC operations

use blake3;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use unicode_normalization::UnicodeNormalization;

/// Hash binary data with BLAKE3
#[pyfunction]
fn hash_blake3(py: Python, data: &[u8]) -> PyResult<PyObject> {
    let hash = blake3::hash(data);
    let hex = hash.to_hex();
    Ok(hex.to_string().into_py(py))
}

/// Hash binary data with keyed BLAKE3
#[pyfunction]
fn hash_blake3_keyed(py: Python, data: &[u8], key: &[u8]) -> PyResult<PyObject> {
    if key.len() != 32 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Key must be exactly 32 bytes"
        ));
    }
    
    let mut key_array = [0u8; 32];
    key_array.copy_from_slice(key);
    
    let mut hasher = blake3::Hasher::new_keyed(&key_array);
    hasher.update(data);
    let hash = hasher.finalize();
    let hex = hash.to_hex();
    
    Ok(hex.to_string().into_py(py))
}

/// Normalize text to Unicode NFC
#[pyfunction]
fn normalize_unicode_nfc(py: Python, text: &str) -> PyResult<PyObject> {
    let normalized: String = text.nfc().collect();
    Ok(normalized.into_py(py))
}

/// Normalize text to Unicode NFD
#[pyfunction]
fn normalize_unicode_nfd(py: Python, text: &str) -> PyResult<PyObject> {
    let normalized: String = text.nfd().collect();
    Ok(normalized.into_py(py))
}

/// Compute Merkle root from sorted hashes
#[pyfunction]
fn compute_merkle_root(py: Python, hashes: Vec<String>) -> PyResult<PyObject> {
    if hashes.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Hash list cannot be empty"
        ));
    }
    
    let mut sorted_hashes = hashes.clone();
    sorted_hashes.sort();
    
    let combined = sorted_hashes.join("");
    let root_hash = blake3::hash(combined.as_bytes());
    
    Ok(root_hash.to_hex().to_string().into_py(py))
}

/// Segment text into grapheme clusters (for stable tokenization)
#[pyfunction]
fn segment_graphemes(py: Python, text: &str) -> PyResult<PyObject> {
    use unicode_segmentation::UnicodeSegmentation;
    
    let graphemes: Vec<String> = text
        .graphemes(true)
        .map(|g| g.to_string())
        .collect();
    
    Ok(graphemes.into_py(py))
}

/// Python module
#[pymodule]
fn cpp_ingestion(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hash_blake3, m)?)?;
    m.add_function(wrap_pyfunction!(hash_blake3_keyed, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_unicode_nfc, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_unicode_nfd, m)?)?;
    m.add_function(wrap_pyfunction!(compute_merkle_root, m)?)?;
    m.add_function(wrap_pyfunction!(segment_graphemes, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_blake3_hash() {
        let data = b"hello world";
        let hash = blake3::hash(data);
        assert_eq!(hash.to_hex().len(), 64); // 32 bytes = 64 hex chars
    }
    
    #[test]
    fn test_unicode_normalization() {
        let text = "café";
        let nfc: String = text.nfc().collect();
        let nfd: String = text.nfd().collect();
        
        assert_ne!(nfc.len(), nfd.len()); // Decomposed form has more chars
    }
}
