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
    page_icon="🎓"
)

conn = get_connection()

# =========================
# STYLE CSS PRO
# =========================
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
}
.card {
    padding: 20px;
    border-radius: 15px;
    background-color: white;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.big-title {
    font-size: 30px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown('<p class="big-title">🎓 Dashboard Gestion des Notes</p>', unsafe_allow_html=True)

menu = st.sidebar.radio("Navigation", [
    "Dashboard", "Étudiants", "Matières", "Notes", "Audit"
])

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.header("📊 Tableau de bord")

    etu = pd.read_sql("SELECT COUNT(*) as total FROM etudiant", conn)
    mat = pd.read_sql("SELECT COUNT(*) as total FROM matiere", conn)
    note = pd.read_sql("SELECT COUNT(*) as total FROM note", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("👨‍🎓 Étudiants", etu["total"][0])
    col2.metric("📘 Matières", mat["total"][0])
    col3.metric("📝 Notes", note["total"][0])

    # Graphique moyenne
    df = pd.read_sql("SELECT nom, moyenne FROM etudiant", conn)

    fig = px.bar(df, x="nom", y="moyenne", title="Moyenne par étudiant")
    st.plotly_chart(fig, use_container_width=True)

# =========================
# ETUDIANTS
# =========================
elif menu == "Étudiants":
    st.header("👨‍🎓 Étudiants")

    col1, col2 = st.columns([1, 2])

    with col1:
        nom = st.text_input("Nom")

        if st.button("Ajouter"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO etudiant(nom) VALUES (%s)", (nom,))
                conn.commit()
            st.success("Ajout réussi")

    with col2:
        df = pd.read_sql("SELECT * FROM etudiant", conn)
        st.dataframe(df, use_container_width=True)

# =========================
# MATIERES
# =========================
elif menu == "Matières":
    st.header("📘 Matières")

    col1, col2 = st.columns([1, 2])

    with col1:
        design = st.text_input("Nom matière")
        coef = st.number_input("Coefficient", min_value=1.0)

        if st.button("Ajouter matière"):
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO matiere(design, coef) VALUES (%s, %s)",
                    (design, coef)
                )
                conn.commit()
            st.success("Ajout réussi")

    with col2:
        df = pd.read_sql("SELECT * FROM matiere", conn)
        st.dataframe(df, use_container_width=True)

# =========================
# NOTES
# =========================
elif menu == "Notes":
    st.header("📝 Notes")

    etu = pd.read_sql("SELECT * FROM etudiant", conn)
    mat = pd.read_sql("SELECT * FROM matiere", conn)

    col1, col2 = st.columns(2)

    # AJOUT
    with col1:
        # =========================
        # AJOUT NOTE
        # =========================
        with col1:
            st.subheader("Ajouter")

            # Étudiants : afficher le nom mais garder l'id
            etu_id = st.selectbox(
                "Étudiant",
                options=etu["id"],        # ce qu'on enregistre
                format_func=lambda x: etu.loc[etu["id"] == x, "nom"].values[0]  # ce qu'on affiche
            )

            # Matières : pareil
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
                st.success("Note ajoutée !")

    # UPDATE DELETE
    with col2:
        st.subheader("Modifier / Supprimer")

        id_mod = st.number_input("ID", min_value=1)
        new_note = st.number_input("Nouvelle note", 0.0, 20.0)

        colA, colB = st.columns(2)

        if colA.button("Modifier"):
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE note SET note=%s WHERE id=%s",
                    (new_note, id_mod)
                )
                conn.commit()
            st.success("Modifiée")

        if colB.button("Supprimer"):
            with conn.cursor() as cur:
                cur.execute("DELETE FROM note WHERE id=%s", (id_mod,))
                conn.commit()
            st.warning("Supprimée")

    # TABLE
    df = pd.read_sql("""
        SELECT n.id, e.nom, m.design, n.note
        FROM note n
        JOIN etudiant e ON n.etudiant_id = e.id
        JOIN matiere m ON n.matiere_id = m.id
    """, conn)

    st.dataframe(df, use_container_width=True)

# =========================
# AUDIT
# =========================
elif menu == "Audit":
    st.header("📊 Audit")

    # Charger données
    df = pd.read_sql("SELECT * FROM audit_note ORDER BY date_op DESC", conn)

    # Statistiques
    stats = pd.read_sql("""
        SELECT
            COUNT(*) FILTER (WHERE operation='INSERT') AS insertions,
            COUNT(*) FILTER (WHERE operation='UPDATE') AS modifications,
            COUNT(*) FILTER (WHERE operation='DELETE') AS suppressions
        FROM audit_note
    """, conn)

    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Insertions", stats['insertions'][0])
    col2.metric("Modifications", stats['modifications'][0])
    col3.metric("Suppressions", stats['suppressions'][0])

    # Renommer les colonnes AVANT
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

    # Ligne TOTAL (avec bons noms)
    summary = {
        "ID": "",
        "Opération": "",
        "Date": "",
        "ID Étudiant": "",
        "ID Matière": "",
        "Ancienne note": "",
        "Nouvelle note": "",
        "Utilisateur": ""
    }

    #
    df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)

    # Affichage
    st.dataframe(df, use_container_width=True)

    col3, col4, col5 = st.columns(3)

    col3.metric("Total des Insertion :", stats['insertions'][0])
    col4.metric("Total des modification :", stats['modifications'][0])
    col5.metric("Total des Suppression : ", stats['suppressions'][0])
