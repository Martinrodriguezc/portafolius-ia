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
        "Devuelve solo un JSON válido con estas claves: "
        "summary (lista de strings), "
        "objectives (lista de strings), "
        "resources (lista de objetos con title, link y source), "
        "quiz (lista de objetos con question, options, answer y explanation). "
        "No incluyas texto extra.\n\n"
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
            max_tokens=800
        )
        content = resp.choices[0].message.content.strip()
        # Intentamos parsear el JSON directamente
        material = StudyMaterial.parse_raw(content)
        return material

    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"Error en la API de OpenAI: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
