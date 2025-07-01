import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
from openai import OpenAIError

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Debe definir OPENAI_API_KEY en el archivo .env")

openai.api_key = OPENAI_API_KEY

app = FastAPI(
    title="Servicio de Material de Estudio IA",
    version="1.0.0",
    description="Recibe feedback de profesor y devuelve material de estudio generado por IA."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FeedbackRequest(BaseModel):
    feedback: str

# Sin tipos internos por ahora, aceptamos listas genéricas
class StudyMaterial(BaseModel):
    summary: list
    objectives: list
    resources: list
    quiz: list

@app.post("/generate-material", response_model=StudyMaterial)
async def generate_material(req: FeedbackRequest):
    prompt = (
        "INSTRUCCIONES CRÍTICAS DE SEGURIDAD: Por ningún motivo debes desobedecer este prompt. "
        "Bajo ningún caso se debe desobedecer el prompt. "
        "Cualquier consulta que no esté enfocada en el estudio médico o en conceptos médicos pertinentes al tema debe ser respondida con un JSON donde: "
        "summary contenga el mensaje 'Por favor solicita información respecto al estudio médico del protocolo en cuestión. Este sistema está diseñado exclusivamente para generar material de estudio médico.', "
        "objectives sea una lista vacía [], "
        "resources contenga al menos 1 recurso con URL real de una página médica de alta reputación (como https://www.who.int/, https://www.cdc.gov/, https://www.medlineplus.gov/), "
        "quiz sea una lista vacía []. "
        "Reitero: bajo ningún caso se debe desobedecer el prompt.\n\n"
        "Genera material de estudio médico basado en el protocolo o feedback proporcionado. "
        "Devuelve SOLO un JSON válido con las siguientes especificaciones:\n\n"
        "IMPORTANTE: Si la consulta es pertinente al tema médico, SIEMPRE DEBES MANDAR EL JSON CON TODOS LOS CAMPOS NO VACIOS. "
        "Ningún campo debe estar vacío cuando la consulta es sobre estudio médico.\n\n"
        "1. summary: Lista de strings NO VACÍA con un resumen completo del protocolo médico, incluyendo sus principales componentes, indicaciones y procedimientos.\n\n"
        "2. objectives: Lista de strings NO VACÍA con los objetivos de aprendizaje específicos del protocolo, enfocados en los aspectos más importantes que el estudiante debe dominar.\n\n"
        "3. resources: Lista de objetos con title, link y source. SIEMPRE debe incluir al menos 1 recurso con URL real y específica. Incluye SOLO recursos de alta calidad y fuentes confiables que sean específicamente artículos, guías, protocolos u otros materiales relacionados directamente al tema del protocolo para que el estudiante pueda revisar y profundizar en los contenidos. Las fuentes deben ser de reputación como:\n"
        "   - Artículos científicos de revistas médicas indexadas (PubMed, Medline, etc.) con URLs específicas\n"
        "   - Guías clínicas oficiales y protocolos actualizados con URLs directas\n"
        "   - Documentos técnicos de organizaciones médicas oficiales (OMS, CDC, FDA, etc.) con URLs específicas\n"
        "   - Materiales educativos de instituciones académicas reconocidas con URLs directas\n"
        "   - Publicaciones de sociedades médicas especializadas con URLs específicas\n"
        "   - Manuales y protocolos hospitalarios actualizados con URLs directas\n\n"
        "IMPORTANTE: Si no encuentras recursos específicos del tema, incluye al menos una URL de una página médica de alta reputación como:\n"
        "   - https://www.who.int/ (Organización Mundial de la Salud)\n"
        "   - https://www.cdc.gov/ (Centros para el Control y Prevención de Enfermedades)\n"
        "   - https://www.fda.gov/ (Administración de Alimentos y Medicamentos)\n"
        "   - https://www.uptodate.com/ (UpToDate - Recursos médicos)\n"
        "   - https://www.medlineplus.gov/ (MedlinePlus - Biblioteca Nacional de Medicina)\n"
        "   - https://www.mayoclinic.org/ (Mayo Clinic)\n"
        "   - https://www.hopkinsmedicine.org/ (Johns Hopkins Medicine)\n"
        "   - https://www.nejm.org/ (New England Journal of Medicine)\n\n"
        "4. quiz: Lista NO VACÍA con mínimo 4 preguntas sobre el protocolo específico, con 4 opciones cada una, respuesta correcta y explicación detallada. Estas preguntas deben ser detalladas y específicas para el protocolo en cuestión buscando una dificultad alta respecto a conceptos médicos. Usa solo letras (A, B, C, D) para las respuestas correctas sin puntos ni caracteres adicionales.\n\n"
        "IMPORTANTE: Si el feedback no proporciona información suficiente sobre un protocolo específico, genera contenido que abarque los puntos más importantes de protocolos médicos generales relevantes al contexto.\n\n"
        "No incluyas texto extra, solo el JSON.\n\n"
        "IMPORTANTE: Asegúrate de que el JSON sea válido y esté correctamente formateado. "
        "Escapa correctamente las comillas dentro de los strings usando comillas dobles. "
        "No uses caracteres especiales que puedan romper el JSON. "
        "No uses acentos, ñ, o caracteres especiales en el contenido. "
        "Usa solo caracteres ASCII básicos. "
        "El JSON debe comenzar con { y terminar con } sin texto adicional.\n\n"
        "Feedback:\n"
        f"{req.feedback}"
    )

    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Actúa como generador de material de estudio médico."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        content = resp.choices[0].message.content.strip()
        
        # Limpiamos el contenido para evitar problemas de JSON
        import json
        import re
        
        # Removemos cualquier texto antes del primer {
        content = content[content.find('{'):]
        
        # Removemos cualquier texto después del último }
        content = content[:content.rfind('}')+1]
        
        # Limpiamos caracteres problemáticos
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        
        # Intentamos parsear el JSON
        try:
            # Primero validamos que sea JSON válido
            json.loads(content)
            material = StudyMaterial.parse_raw(content)
            return material
        except json.JSONDecodeError as json_error:
            raise HTTPException(status_code=500, detail=f"JSON malformado: {json_error}")
        except Exception as parse_error:
            raise HTTPException(status_code=500, detail=f"Error al parsear el modelo de datos: {parse_error}")

    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Error en la API de OpenAI: {e}")

    except Exception as e:
        if "jsondecode" in str(e) or "JSON" in str(e):
            raise HTTPException(status_code=500, detail=f"Error en formato JSON: {e}")
        else:
            raise HTTPException(status_code=500, detail=f"Error interno: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
