import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_connection

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Gestion Notes Pro",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🎓"
)

conn = get_connection()

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.card {
    padding: 20px;
    border-radius: 12px;
    background: white;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title(" Gestion des Notes")

menu = st.sidebar.radio("Menu", [
    "Dashboard", "Étudiants", "Matières", "Notes", "Audit"
])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.header("Tableau de bord")

    etu = pd.read_sql("SELECT COUNT(*) as total FROM etudiant", conn)
    mat = pd.read_sql("SELECT COUNT(*) as total FROM matiere", conn)
    note = pd.read_sql("SELECT COUNT(*) as total FROM note", conn)

    col1, col2, col3 = st.columns(3)
    col1.metric("Étudiants", etu["total"][0])
    col2.metric("Matières", mat["total"][0])
    col3.metric("Notes", note["total"][0])

    df = pd.read_sql("SELECT nom, moyenne FROM etudiant", conn)
    fig = px.bar(df, x="nom", y="moyenne")
    st.plotly_chart(fig, use_container_width=True)

# =========================
# ETUDIANTS
# =========================
elif menu == "Étudiants":
    st.header("Gestion des Étudiants")

    # FORMULAIRE AJOUT
    st.subheader("Ajouter un étudiant")
    nom = st.text_input("Nom étudiant")

    if st.button("Ajouter étudiant"):
        if nom.strip() != "":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO etudiant(nom) VALUES (%s)", (nom,))
                conn.commit()
            st.success("Étudiant ajouté avec succès")
        else:
            st.error("Le nom ne peut pas être vide")

    # FORMULAIRE MODIFICATION
    st.subheader(" Modifier un étudiant")
    df_etu = pd.read_sql("SELECT * FROM etudiant", conn)
    etu_id = st.selectbox("Sélectionnez un étudiant", options=df_etu["id"], format_func=lambda x: df_etu.loc[df_etu["id"]==x, "nom"].values[0])
    new_nom = st.text_input("Nouveau nom", value=df_etu.loc[df_etu["id"]==etu_id, "nom"].values[0])

    if st.button("Modifier étudiant"):
        with conn.cursor() as cur:
            cur.execute("UPDATE etudiant SET nom=%s WHERE id=%s", (new_nom, etu_id))
            conn.commit()
        st.success("Étudiant modifié")

    # FORMULAIRE SUPPRESSION
    st.subheader("🗑 Supprimer un étudiant")
    del_id = st.selectbox("Étudiant à supprimer", options=df_etu["id"], format_func=lambda x: df_etu.loc[df_etu["id"]==x, "nom"].values[0])

    if st.button("Supprimer étudiant"):
        with conn.cursor() as cur:
            cur.execute("DELETE FROM etudiant WHERE id=%s", (del_id,))
            conn.commit()
        st.warning("Étudiant supprimé")

    # TABLEAU
    st.subheader("📋 Liste des étudiants")
    st.dataframe(df_etu, use_container_width=True)

# =========================
# MATIERES
# =========================
elif menu == "Matières":
    st.header(" Gestion des Matières")

    # FORMULAIRE AJOUT
    st.subheader(" Ajouter une matière")
    design = st.text_input("Nom matière")
    coef = st.number_input("Coefficient", min_value=1.0, step=0.1)

    if st.button("Ajouter matière"):
        if design.strip() != "":
            with conn.cursor() as cur:
                cur.execute("INSERT INTO matiere(design, coef) VALUES (%s, %s)", (design, coef))
                conn.commit()
            st.success("Matière ajoutée")
        else:
            st.error("Le nom de la matière ne peut pas être vide")

    # FORMULAIRE MODIFICATION
    st.subheader(" Modifier une matière")
    df_mat = pd.read_sql("SELECT * FROM matiere", conn)
    mat_id = st.selectbox("Sélectionnez une matière", options=df_mat["id"], format_func=lambda x: df_mat.loc[df_mat["id"]==x, "design"].values[0])
    new_design = st.text_input("Nouveau nom", value=df_mat.loc[df_mat["id"]==mat_id, "design"].values[0])
    new_coef = st.number_input("Nouveau coefficient", min_value=1.0, step=0.1, value=float(df_mat.loc[df_mat["id"]==mat_id, "coef"].values[0]))

    if st.button("Modifier matière"):
        with conn.cursor() as cur:
            cur.execute("UPDATE matiere SET design=%s, coef=%s WHERE id=%s", (new_design, new_coef, mat_id))
            conn.commit()
        st.success("Matière modifiée")

    # FORMULAIRE SUPPRESSION
    st.subheader("🗑 Supprimer une matière")
    del_mat_id = st.selectbox("Matière à supprimer", options=df_mat["id"], format_func=lambda x: df_mat.loc[df_mat["id"]==x, "design"].values[0])

    if st.button("Supprimer matière"):
        with conn.cursor() as cur:
            cur.execute("DELETE FROM matiere WHERE id=%s", (del_mat_id,))
            conn.commit()
        st.warning("Matière supprimée")

    # TABLEAU
    st.subheader(" Liste des matières")
    st.dataframe(df_mat, use_container_width=True)

# =========================
# NOTES
# =========================
elif menu == "Notes":
    st.header(" Gestion des Notes")

    etu = pd.read_sql("SELECT * FROM etudiant", conn)
    mat = pd.read_sql("SELECT * FROM matiere", conn)

    # FORMULAIRE AJOUT
    st.subheader(" Ajouter une note")

    etu_id = st.selectbox(
        "Étudiant",
        options=etu["id"],
        format_func=lambda x: etu.loc[etu["id"] == x, "nom"].values[0]
    )

    mat_id = st.selectbox(
        "Matière",
        options=mat["id"],
        format_func=lambda x: mat.loc[mat["id"] == x, "design"].values[0]
    )

    note = st.number_input("Note", 0.0, 20.0)

    if st.button("Ajouter note"):
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO note(etudiant_id, matiere_id, note) VALUES (%s, %s, %s)",
                (etu_id, mat_id, note)
            )
            conn.commit()
        st.success("Note ajoutée")

    # MODIFIER / SUPPRIMER
    st.subheader(" Modifier / Supprimer")

    id_mod = st.number_input("ID note", min_value=1)
    new_note = st.number_input("Nouvelle note", 0.0, 20.0)

    col1, col2 = st.columns(2)

    if col1.button("Modifier"):
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE note SET note=%s WHERE id=%s",
                (new_note, id_mod)
            )
            conn.commit()
        st.success("Modifiée")

    if col2.button("Supprimer"):
        with conn.cursor() as cur:
            cur.execute("DELETE FROM note WHERE id=%s", (id_mod,))
            conn.commit()
        st.warning("Supprimée")

    # TABLEAU
    st.subheader(" Liste des notes")

    df = pd.read_sql("""
        SELECT n.id, e.nom AS Étudiant, m.design AS Matière, n.note
        FROM note n
        JOIN etudiant e ON n.etudiant_id = e.id
        JOIN matiere m ON n.matiere_id = m.id
    """, conn)

    st.dataframe(df, use_container_width=True)

# =========================
# AUDIT
# =========================
elif menu == "Audit":
    st.header(" Audit")

    df = pd.read_sql("SELECT * FROM audit_note ORDER BY date_op DESC", conn)

    stats = pd.read_sql("""
        SELECT
            COUNT(*) FILTER (WHERE operation='INSERT') AS insertions,
            COUNT(*) FILTER (WHERE operation='UPDATE') AS modifications,
            COUNT(*) FILTER (WHERE operation='DELETE') AS suppressions
        FROM audit_note
    """, conn)

    # TABLEAU
    st.subheader(" Historique")

    df = df.rename(columns={
        "id": "ID",
        "operation": "Opération",
        "date_op": "Date",
        "etudiant_id": "ID Étudiant",
        "matiere_id": "ID Matière",
        "note_ancien": "Ancienne note",
        "note_nouv": "Nouvelle note",
        "utilisateur": "Utilisateur"
    })

    st.dataframe(df, use_container_width=True)

    # STATS EN BAS
    st.subheader(" Statistiques")

    col1, col2, col3 = st.columns(3)

    col1.success(f"Insertions : {stats['insertions'][0]}")
    col2.info(f"Modifications : {stats['modifications'][0]}")
    col3.error(f"Suppressions : {stats['suppressions'][0]}")
