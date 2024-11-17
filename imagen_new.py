import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
from PIL import Image
import tempfile
from datetime import datetime

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

# Rutas de archivos CSV
dataset_path = "imagenes/imagenes.csv"
new_dataset_path = "imagenes/nuevas_descripciones.csv"

# Cargar o inicializar los DataFrames
df = pd.read_csv(dataset_path, delimiter=';', encoding='ISO-8859-1')
if os.path.exists(new_dataset_path):
    new_df = pd.read_csv(new_dataset_path, delimiter=';', encoding='ISO-8859-1')
else:
    new_df = pd.DataFrame(columns=["imagen", "descripcion", "generated_description", "fecha"])

# Prompt para generar descripciones concisas
describe_system_prompt = '''
Eres un sistema especializado en generar descripciones breves y precisas para escenas culturales y eventos andinos, especialmente de la festividad de la Mamacha Carmen en Paucartambo. Describe de manera clara y objetiva la escena principal, destacando solo los elementos visibles y relevantes sin adornos adicionales. Mantente directo y conciso.
'''

# Función para combinar ejemplos
def get_combined_examples(df):
    if 'generated_description' not in df.columns:
        return "No hay descripciones generadas previas."
    combined_examples = "Ejemplos de descripciones previas:\n\n"
    for _, row in df.iterrows():
        if pd.notna(row.get('generated_description')) and pd.notna(row.get('descripcion')):
            combined_examples += f"Título: {row['descripcion']}\nDescripción: {row['generated_description']}\n\n"
    return combined_examples

# Función para describir imagen
def describe_image(img_url, title, example_descriptions):
    prompt = f"{describe_system_prompt}\n\n{example_descriptions}\n\nGenera una descripción para la siguiente imagen:\nTítulo: {title}"
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": describe_system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# Función para generar preguntas dinámicas
def generate_questions_from_description(description):
    questions = [
        f"¿Qué elementos destacan en '{description[:50]}...'?",
        f"¿Cuál es el contexto cultural de esta escena?",
        "¿Qué simbolismo tiene esta imagen?"
    ]
    return questions

# Inicializar la aplicación Streamlit
st.title("Generador de Descripciones de Imágenes de Danzas de Paucartambo")

# Sidebar para historial y opciones
with st.sidebar:
    st.subheader("Opciones")
    if st.checkbox("Mostrar historial"):
        if new_df.empty:
            st.info("No hay descripciones generadas aún.")
        else:
            st.dataframe(new_df[["imagen", "descripcion", "generated_description"]])

# Método de carga de imágenes
option = st.radio("Seleccione el método para proporcionar una imagen:", ("URL de imagen", "Subir imagen"))

if option == "URL de imagen":
    img_url = st.text_input("Ingrese la URL de la imagen")
    if img_url:
        st.image(img_url, caption="Imagen desde URL", use_column_width=True)

    title = st.text_input("Ingrese un título o descripción breve de la imagen")
    if title:
        example_descriptions = get_combined_examples(new_df)
        if st.button("Generar Descripción"):
            with st.spinner("Generando descripción..."):
                try:
                    description = describe_image(img_url, title, example_descriptions)
                    st.success("Descripción generada con éxito.")
                    st.write("Descripción en español:")
                    st.write(description)

                    new_row = {
                        "imagen": img_url,
                        "descripcion": title,
                        "generated_description": description,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
                    new_df.to_csv(new_dataset_path, sep=';', index=False, encoding='ISO-8859-1')

                    dynamic_questions = generate_questions_from_description(description)
                    st.write("**Preguntas relacionadas:**")
                    for q in dynamic_questions:
                        if st.button(q):
                            st.write(f"Respuesta a: {q}")  # Placeholder
                except Exception as e:
                    st.error(f"Error al generar la descripción: {e}")
else:
    uploaded_file = st.file_uploader("Cargue una imagen", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada", use_column_width=True)

        title = st.text_input("Ingrese un título o descripción breve de la imagen")
        if title:
            example_descriptions = get_combined_examples(new_df)
            if st.button("Generar Descripción"):
                with st.spinner("Generando descripción..."):
                    try:
                        # Guardar temporalmente la imagen
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                            temp_file.write(uploaded_file.getbuffer())
                            img_url = temp_file.name

                        description = describe_image(img_url, title, example_descriptions)
                        st.success("Descripción generada con éxito.")
                        st.write("Descripción en español:")
                        st.write(description)

                        new_row = {
                            "imagen": img_url,
                            "descripcion": title,
                            "generated_description": description,
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
                        new_df.to_csv(new_dataset_path, sep=';', index=False, encoding='ISO-8859-1')

                        dynamic_questions = generate_questions_from_description(description)
                        st.write("**Preguntas relacionadas:**")
                        for q in dynamic_questions:
                            if st.button(q):
                                st.write(f"Respuesta a: {q}")  # Placeholder
                    except Exception as e:
                        st.error(f"Error al generar la descripción: {e}")
