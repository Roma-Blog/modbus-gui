use pyo3::prelude::*;
use pyo3::types::PyDict;
use serialport::SerialPort;
use std::time::Duration;

/// Вычисляет CRC16 для Modbus RTU
fn calculate_crc16(data: &[u8]) -> u16 {
    let mut crc: u16 = 0xFFFF;
    for byte in data {
        crc ^= *byte as u16;
        for _ in 0..8 {
            if crc & 0x0001 != 0 {
                crc = (crc >> 1) ^ 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }
    crc
}

/// Создаёт запрос Modbus команды 17 (Read Device Identification)
fn create_command_17(device_address: u8) -> Vec<u8> {
    let mut request = vec![
        device_address,
        0x11, // Функция 17
        0x00,
        0x00,
        0x00,
        0x00,
    ];
    
    let crc = calculate_crc16(&request);
    request.extend_from_slice(&crc.to_le_bytes());
    request
}

/// Проверяет ответ от устройства
fn validate_response(response: &[u8], device_address: u8) -> bool {
    if response.len() < 7 {
        return false;
    }
    
    // Проверка адреса и функции
    if response[0] != device_address || response[1] != 0x11 {
        return false;
    }
    
    // Проверка CRC
    let response_crc = u16::from_le_bytes([response[response.len() - 2], response[response.len() - 1]]);
    let calculated_crc = calculate_crc16(&response[..response.len() - 2]);
    
    response_crc == calculated_crc
}

/// Результат сканирования
#[derive(Clone)]
pub struct ScanResult {
    pub address: u8,
    pub baudrate: u32,
    pub response: String,
}

/// Пытается получить ответ от устройства на указанной скорости и адресе
fn try_device_detection(
    port_name: &str,
    baudrate: u32,
    device_address: u8,
    timeout_ms: u64,
) -> Option<ScanResult> {
    // Открываем порт с минимальными настройками
    let mut port = match serialport::new(port_name, baudrate)
        .timeout(Duration::from_millis(timeout_ms))
        .open()
    {
        Ok(p) => p,
        Err(_) => return None,
    };
    
    // Очищаем буферы
    let _ = port.clear(serialport::ClearBuffer::All);
    
    // Создаём и отправляем запрос
    let request = create_command_17(device_address);
    if port.write(&request).is_err() {
        return None;
    }
    let _ = port.flush();
    
    // Пауза для ответа устройства (200ms как в Python коде)
    std::thread::sleep(Duration::from_millis(200));
    
    // Читаем ответ
    let mut response = Vec::new();
    let mut buf = [0u8; 256];
    
    // Читаем пока есть данные или не истечёт таймаут
    loop {
        match port.bytes_to_read() {
            Ok(n) if n > 0 => {
                match port.read(&mut buf[..n as usize]) {
                    Ok(read) => {
                        response.extend_from_slice(&buf[..read]);
                    }
                    Err(_) => break,
                }
                // Небольшая пауза между чтениями
                std::thread::sleep(Duration::from_millis(10));
            }
            _ => break,
        }
    }
    
    if validate_response(&response, device_address) {
        Some(ScanResult {
            address: device_address,
            baudrate,
            response: response.iter().map(|b| format!("{:02X}", b)).collect::<Vec<_>>().join(" "),
        })
    } else {
        None
    }
}

/// Быстрый сканер Modbus RTU устройств
#[pyclass]
pub struct ModbusScanner {
    port_name: String,
    timeout_ms: u64,
}

#[pymethods]
impl ModbusScanner {
    /// Создаёт новый сканер
    #[new]
    fn new(port_name: &str, timeout_ms: u64) -> Self {
        ModbusScanner {
            port_name: port_name.to_string(),
            timeout_ms,
        }
    }
    
    /// Сканирует один адрес на одной скорости
    fn scan_single(&self, address: u8, baudrate: u32) -> Option<ScanResultPy> {
        try_device_detection(&self.port_name, baudrate, address, self.timeout_ms)
            .map(|r| ScanResultPy {
                address: r.address,
                baudrate: r.baudrate,
                response: r.response,
            })
    }
    
    /// Сканирует диапазон адресов на одной скорости
    /// 
    /// Args:
    ///     baudrate: Скорость соединения
    ///     start_address: Начальный адрес (включительно)
    ///     end_address: Конечный адрес (включительно)
    ///     status_callback: Python функция для обновления статуса (опционально)
    /// 
    /// Returns:
    ///     Список найденных устройств
    fn scan_addresses(
        &self,
        baudrate: u32,
        start_address: u8,
        end_address: u8,
        status_callback: Option<PyObject>,
    ) -> PyResult<Vec<ScanResultPy>> {
        let mut results = Vec::new();
        
        for address in start_address..=end_address {
            // Обновляем статус через callback
            if let Some(callback) = &status_callback {
                Python::with_gil(|py| {
                    let _ = callback.call1(py, (format!("Проверка адреса {}...", address),));
                });
            }
            
            if let Some(result) = try_device_detection(&self.port_name, baudrate, address, self.timeout_ms) {
                results.push(ScanResultPy {
                    address: result.address,
                    baudrate: result.baudrate,
                    response: result.response,
                });
            }
        }
        
        Ok(results)
    }
    
    /// Сканирует все комбинации адресов и скоростей
    /// 
    /// Args:
    ///     baudrates: Список скоростей для проверки
    ///     start_address: Начальный адрес (включительно)
    ///     end_address: Конечный адрес (включительно)
    ///     status_callback: Python функция для обновления статуса (опционально)
    /// 
    /// Returns:
    ///     Список найденных устройств
    fn scan_all(
        &self,
        baudrates: Vec<u32>,
        start_address: u8,
        end_address: u8,
        status_callback: Option<PyObject>,
    ) -> PyResult<Vec<ScanResultPy>> {
        let mut results = Vec::new();
        
        for baudrate in baudrates {
            if let Some(callback) = &status_callback {
                Python::with_gil(|py| {
                    let _ = callback.call1(py, (format!("Проверка скорости {}...", baudrate),));
                });
            }
            
            for address in start_address..=end_address {
                if let Some(callback) = &status_callback {
                    Python::with_gil(|py| {
                        let _ = callback.call1(py, (format!("  Адрес {}/{}...", address, end_address),));
                    });
                }
                
                if let Some(result) = try_device_detection(&self.port_name, baudrate, address, self.timeout_ms) {
                    results.push(ScanResultPy {
                        address: result.address,
                        baudrate: result.baudrate,
                        response: result.response,
                    });
                }
            }
        }
        
        Ok(results)
    }
    
    /// Сканирует одну скорость и возвращает первое найденное устройство
    fn scan_first_found(
        &self,
        baudrate: u32,
        start_address: u8,
        end_address: u8,
        status_callback: Option<PyObject>,
    ) -> PyResult<Option<ScanResultPy>> {
        for address in start_address..=end_address {
            if let Some(callback) = &status_callback {
                Python::with_gil(|py| {
                    let _ = callback.call1(py, (format!("Проверка адреса {}...", address),));
                });
            }
            
            if let Some(result) = try_device_detection(&self.port_name, baudrate, address, self.timeout_ms) {
                return Ok(Some(ScanResultPy {
                    address: result.address,
                    baudrate: result.baudrate,
                    response: result.response,
                }));
            }
        }
        
        Ok(None)
    }
}

/// Python-представление результата сканирования
#[pyclass]
#[derive(Clone)]
pub struct ScanResultPy {
    #[pyo3(get)]
    pub address: u8,
    #[pyo3(get)]
    pub baudrate: u32,
    #[pyo3(get)]
    pub response: String,
}

#[pymethods]
impl ScanResultPy {
    fn __repr__(&self) -> String {
        format!(
            "ScanResult(address={}, baudrate={}, response='{}')",
            self.address, self.baudrate, self.response
        )
    }
    
    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new(py);
        dict.set_item("address", self.address)?;
        dict.set_item("baudrate", self.baudrate)?;
        dict.set_item("response", &self.response)?;
        Ok(dict.into())
    }
}

/// Модуль для быстрого сканирования Modbus RTU устройств
#[pymodule]
fn modbus_scanner_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<ModbusScanner>()?;
    m.add_class::<ScanResultPy>()?;
    
    // Функция для быстрого поиска устройства
    #[pyfn(m)]
    #[pyo3(name = "quick_scan")]
    fn quick_scan_py(
        port_name: &str,
        baudrates: Vec<u32>,
        start_address: u8,
        end_address: u8,
        timeout_ms: u64,
        status_callback: Option<PyObject>,
    ) -> PyResult<Vec<ScanResultPy>> {
        let scanner = ModbusScanner::new(port_name, timeout_ms);
        scanner.scan_all(baudrates, start_address, end_address, status_callback)
    }
    
    Ok(())
}
