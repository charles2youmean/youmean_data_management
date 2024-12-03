
#------
# Lecture d'un pdf et extraction du texte
#------

import PyPDF2

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text


#------
# Segmeter le texte en phrases propres
#------

import re

def clean_and_split_text(text):
    # Supprime les retours à la ligne non nécessaires
    text = re.sub(r'(?<!\.\n)(?<!\n\n)\n', ' ', text)
    # Segmente le texte en phrases
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


#------
# Généner un Excel
#------

import pandas as pd

def save_to_excel(sentences, pdf_name, output_path="output.xlsx"):
    data = {"Texte": sentences, "Source": [pdf_name] * len(sentences)}
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    print(f"Fichier Excel enregistré sous : {output_path}")


#------
# Interface Streamlit
#------

import os
from PyPDF2 import PdfReader
import pandas as pd
import re
import streamlit as st

#CSS mise en page streamlit
from PIL import Image
import base64

# Charger l'image du logo (fichier dans le même dossier que le script)
logo_path = "Favicon HD bleu-OK.png"
with open(logo_path, "rb") as image_file:
    logo_base64 = base64.b64encode(image_file.read()).decode("utf-8")

# CSS pour unifier les couleurs de la bande grise
st.sidebar.markdown(
    """
    <style>
        /* Style de la barre latérale */
        .sidebar {
            background-color: #f0f0f0; /* Gris clair uniforme */
            padding: 20px;
            text-align: center;
        }

        /* Uniformisation de l'arrière-plan dans la barre */
        section[data-testid="stSidebar"] > div:first-child {
            background-color: #f0f0f0; /* Appliquer la même couleur grise */
        }

        /* Style du logo et du texte */
        .sidebar img {
            width: 80px;
            margin-bottom: 15px;
        }

        .sidebar-text {
            font-size: 18px;
            font-weight: bold;
            color: #333333;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# HTML pour afficher le logo et le texte
st.sidebar.markdown(
    f"""
    <div class="sidebar">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo">
        <div class="sidebar-text">Youmean Data Management Solutions</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Fonctions
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def clean_and_split_text(text):
    text = re.sub(r'(?<!\.\n)(?<!\n\n)\n', ' ', text)
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def save_to_excel(sentences, pdf_name, output_folder="."):
    base_name = os.path.splitext(pdf_name)[0]
    output_path = os.path.join(output_folder, f"{base_name}.xlsx")
    data = {"Texte": sentences, "Source": [pdf_name] * len(sentences)}
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    return output_path

# Interface Streamlit
st.title("Extraction et nettoyage de PDF vers Excel")
uploaded_files = st.file_uploader("Déposez un ou plusieurs PDF ici", accept_multiple_files=True, type="pdf")

if st.button("Lancer l'extraction"):
    if uploaded_files:
        output_files = []
        for uploaded_file in uploaded_files:
            pdf_name = uploaded_file.name
            text = extract_text_from_pdf(uploaded_file)
            sentences = clean_and_split_text(text)
            output_path = save_to_excel(sentences, pdf_name)
            output_files.append(output_path)

        # Génère les liens de téléchargement
        if output_files:
            st.success("Extraction terminée.")
            for output_file in output_files:
                with open(output_file, "rb") as f:
                    st.download_button(
                        label=f"Télécharger {os.path.basename(output_file)}",
                        data=f,
                        file_name=os.path.basename(output_file),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    else:
        st.warning("Veuillez uploader au moins un fichier PDF.")