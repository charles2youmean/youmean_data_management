#------ Importation des modules nécessaires ------#
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract_text
import pandas as pd
import re
import os
import string
import streamlit as st
from PIL import Image
import base64


#######APPLI 1 PDF VERS EXCEL#########

#------ Fonction pour l'extraction de texte avec pdfplumber ------#
def extract_text_with_pdfplumber(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text.strip()
    except Exception as e:
        return None


#------ Fonction principale d'extraction ------#
def extract_text_from_pdf(pdf_file):
    text = extract_text_with_pdfplumber(pdf_file)
    if not text:
        text = extract_text_with_pdfminer(pdf_file)
    return text

#------ Fonction pour nettoyer et segmenter le texte ------#
def clean_and_split_text(text):
    """
    Nettoie et segmente le texte en phrases individuelles.
    """
    # Supprime les retours à la ligne inutiles
    text = re.sub(r'(?<!\.\n)(?<!\n\n)\n', ' ', text)
    # Segmente le texte en phrases basées sur la ponctuation
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


#------ Fonction pour vérifier texte aberrant ------#
def is_text_aberrant(text, threshold=0.7):
    if not text:
        return True
    total_characters = len(text)
    alphabetic_characters = sum(1 for char in text if char.isalpha())
    alphabetic_ratio = alphabetic_characters / total_characters if total_characters > 0 else 0
    return alphabetic_ratio < threshold

#------ Fonction pour remplacer les puces par des retours à la ligne ------#
def replace_bullets_with_newlines(text, symbols):
    """
    Remplace les puces ou caractères spéciaux par des retours à la ligne.
    """
    pattern = f"({'|'.join(re.escape(symbol) for symbol in symbols)})"
    text = re.sub(pattern, r'\n\1', text)
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    return text

#------ Fonction pour sauvegarder en Excel ------#
def save_combined_to_excel(sentences_sources, output_path):
    data = {
        "Texte": [s[0] for s in sentences_sources],
        "Source": [s[1] for s in sentences_sources],
    }
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    return output_path

#------ Interface Streamlit ------#
st.title("Extraction et nettoyage de PDF vers un Excel sourcé")

# CSS pour personnaliser la barre latérale
logo_path = "Favicon HD bleu-OK.png"
with open(logo_path, "rb") as image_file:
    logo_base64 = base64.b64encode(image_file.read()).decode("utf-8")

st.sidebar.markdown(
    """
    <style>
        .sidebar {
            background-color: #f0f0f0;
            padding: 20px;
            text-align: center;
        }
        section[data-testid="stSidebar"] > div:first-child {
            background-color: #f0f0f0;
        }
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

st.sidebar.markdown(
    f"""
    <div class="sidebar">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo">
        <div class="sidebar-text">Youmean Data Management Tools</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Téléchargement de fichiers PDF
uploaded_files = st.file_uploader(
    "Déposez un ou plusieurs fichiers PDF", 
    accept_multiple_files=True, 
    type="pdf",
    key="unique_file_uploader"
)

# Bouton pour lancer l'extraction
if st.button("Lancer l'extraction", key="extract_button"):
    if uploaded_files:
        sentences_sources = []
        file_statuses = []  # Liste des statuts des fichiers

        for uploaded_file in uploaded_files:
            pdf_name = uploaded_file.name
            text = extract_text_from_pdf(uploaded_file)

            if text is None or is_text_aberrant(text):
                # Ajouter une alerte dans l'Excel
                sentences_sources.append((f"❌ATTENTION❌ : Fichier non lisible par l'application YOUMEAN ({pdf_name})", pdf_name))
                file_statuses.append((pdf_name, "❌ Données aberrantes"))
            else:
                file_statuses.append((pdf_name, "✅ Extraction réussie"))
                text = replace_bullets_with_newlines(text, symbols=["•", "*", "-", "→"])
                sentences = clean_and_split_text(text)
                sentences_sources.extend([(sentence, pdf_name) for sentence in sentences])

        # Déterminer le nom du fichier de sortie
        if len(uploaded_files) == 1:
            base_name = os.path.splitext(uploaded_files[0].name)[0]
            output_path = f"{base_name}.xlsx"
        else:
            output_path = "multiples_sources.xlsx"

        if sentences_sources:
            save_combined_to_excel(sentences_sources, output_path)
            st.success("Extraction terminée.")

            # Afficher le statut des fichiers traités
            st.subheader("Statut des fichiers traités :")
            for file_name, status in file_statuses:
                if "✅" in status:
                    st.success(f"{file_name} : {status}")
                else:
                    st.error(f"{file_name} : {status}")

            # Bouton pour télécharger le fichier Excel
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"Télécharger {output_path}",
                    data=f,
                    file_name=output_path,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("Veuillez uploader au moins un fichier PDF.")


#######APPLI 2 DIVERSITE LEXICALE#########

import streamlit as st
import pandas as pd
import numpy as np
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk

# Téléchargement des modèles NLTK nécessaires
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

# Interface Streamlit
st.title("Analyse comparative de textes")

# Téléchargement de plusieurs fichiers texte
uploaded_txt_files = st.file_uploader(
    "Téléchargez jusqu'à 10 fichiers texte (.txt)",
    type="txt",
    accept_multiple_files=True,
    key="multiple_txt_file_uploader"
)

# Vérification du nombre de fichiers
if uploaded_txt_files and len(uploaded_txt_files) <= 10:
    results = []

    for uploaded_file in uploaded_txt_files:
        # Lecture du contenu du fichier
        text_content = uploaded_file.read().decode("utf-8")
        
        # Analyse du texte
        sentences = sent_tokenize(text_content)
        sentence_lengths = [len(word_tokenize(sentence)) for sentence in sentences]

        # Calculs statistiques
        avg_length = round(np.mean(sentence_lengths), 2)
        median_length = round(np.median(sentence_lengths), 2)
        min_length = round(np.min(sentence_lengths), 2)
        max_length = round(np.max(sentence_lengths), 2)
        std_length = round(np.std(sentence_lengths), 2)

        # Calcul de la richesse lexicale (Herdan)
        tokens = word_tokenize(text_content)
        unique_tokens = set(tokens)
        herdans_c = round(np.log(len(unique_tokens)) / np.log(len(tokens)), 2) if len(tokens) > 0 else 0

        # Ajout des résultats au tableau comparatif
        results.append({
            "Nom du fichier": uploaded_file.name,
            "Moyenne des mots par phrase": avg_length,
            "Médiane des mots par phrase": median_length,
            "Minimum des mots par phrase": min_length,
            "Maximum des mots par phrase": max_length,
            "Écart type des mots par phrase": std_length,
            "Total de mots": len(tokens),
            "Mots uniques": len(unique_tokens),
            "Herdan's C": herdans_c
        })

    # Conversion en DataFrame
    comparison_df = pd.DataFrame(results)

    # Formater les nombres selon la convention française
    st.subheader("Tableau comparatif des textes")
    st.dataframe(comparison_df.style.format({
        "Moyenne des mots par phrase": "{:,.2f}".format,
        "Médiane des mots par phrase": "{:,.2f}".format,
        "Minimum des mots par phrase": "{:,.2f}".format,
        "Maximum des mots par phrase": "{:,.2f}".format,
        "Écart type des mots par phrase": "{:,.2f}".format,
        "Herdan's C": "{:,.2f}".format
    }, decimal=",", thousands=" "))

else:
    st.info("Veuillez télécharger jusqu'à 10 fichiers texte (.txt).")
