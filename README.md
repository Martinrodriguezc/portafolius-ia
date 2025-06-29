## Instalación

1. **Clona este repositorio:**
    ```bash
    git clone https://github.com/Martinrodriguezc/portafolius-anonymizer-service.git
    cd portafolius-anonymizer-service
    ```

2. **Crea y activa un entorno virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Instala dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4. **(Opcional, solo si usas OCR) Instala Tesseract OCR:**

    - En MacOS: `brew install tesseract`
    - En Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
    - En Windows: [Descarga aquí](https://github.com/tesseract-ocr/tesseract/wiki)

## Uso

1. **Corre el microservicio:**
    ```bash
    uvicorn main:app --reload
    ```