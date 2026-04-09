import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_connection
from supabase import create_client

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
# SUPABASE CONFIG
# =========================
SUPABASE_URL = "https://pjkssbogwfbnskuxxljb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqa3NzYm9nd2ZibnNrdXh4bGpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzA3ODAsImV4cCI6MjA5MDIwNjc4MH0.u5v-H5ASgnWupWadJ6tpGrpqiImDfZ5nAuh5yh-KmUY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# SESSION
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# LOGIN
# =========================
if st.session_state.user is None:

    st.title("🔐 Connexion")

    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                st.session_state.user = res.user
                st.success("Connexion réussie")
                st.rerun()
            else:
                st.error("Email ou mot de passe incorrect")

        except Exception as e:
            st.error(f"Erreur: {str(e)}")

    st.stop()

# =========================
# ROLE USER
# =========================
def get_user_role(user_id):
    try:
        res = supabase.table("profiles").select("role").eq("id", user_id).execute()
        if res.data:
            return res.data[0]["role"]
        return "user"
    except:
        return "user"

role = get_user_role(st.session_state.user.id)
username = get_user_role(st.session_state.user.id)

# =========================
# SIDEBAR
# =========================
st.sidebar.write(f"{st.session_state.user.email} ({role})")

if st.sidebar.button("Déconnexion"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

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

st.title("Gestion des Notes")

# =========================
# MENU SELON ROLE
# =========================
if role == "admin":
    menu = st.sidebar.radio("Menu", ["Audit"])
elif role == "user":
    menu = st.sidebar.radio("Menu", [
        "Étudiants", "Matières", "Notes"
    ])
else:
    st.error("Rôle inconnu")
    st.stop()


# =========================
# ETUDIANTS
# =========================
if menu == "Étudiants":
    st.header("Gestion des Étudiants")

    nom = st.text_input("Nom étudiant")

    if st.button("Ajouter étudiant"):
        if nom.strip():
            with conn.cursor() as cur:
                cur.execute("INSERT INTO etudiant(nom) VALUES (%s)", (nom,))

                # AUDIT avec utilisateur connecté
                cur.execute("""
                    INSERT INTO audit_note(operation, utilisateur, date_op)
                    VALUES (%s, %s, NOW())
                """, ("INSERT", username))

                conn.commit()
            st.success("Ajouté")
        else:
            st.error("Nom vide")

    df_etu = pd.read_sql("SELECT * FROM etudiant", conn)

    etu_id = st.selectbox("Étudiant", df_etu["id"],
        format_func=lambda x: df_etu.loc[df_etu["id"]==x, "nom"].values[0])

    new_nom = st.text_input("Nouveau nom",
        value=df_etu.loc[df_etu["id"]==etu_id, "nom"].values[0])

    if st.button("Modifier étudiant"):
        with conn.cursor() as cur:
            cur.execute("UPDATE etudiant SET nom=%s WHERE id=%s", (new_nom, etu_id))

            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("UPDATE", username))

            conn.commit()
        st.success("Modifié")

    del_id = st.selectbox("Supprimer", df_etu["id"],
        format_func=lambda x: df_etu.loc[df_etu["id"]==x, "nom"].values[0])

    if st.button("Supprimer étudiant"):
        with conn.cursor() as cur:
            cur.execute("DELETE FROM etudiant WHERE id=%s", (del_id,))
            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("DELETE", username))

            conn.commit()
        st.warning("Supprimé")

    st.dataframe(df_etu)

# =========================
# MATIERES
# =========================
elif menu == "Matières":
    st.header("Gestion des Matières")

    design = st.text_input("Nom matière")
    coef = st.number_input("Coefficient", min_value=1.0)

    if st.button("Ajouter matière"):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO matiere(design, coef) VALUES (%s, %s)", (design, coef))

            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("INSERT", username))

            conn.commit()
        st.success("Ajoutée")

    df_mat = pd.read_sql("SELECT * FROM matiere", conn)

    st.dataframe(df_mat)

# =========================
# NOTES
# =========================
elif menu == "Notes":
    st.header("Gestion des Notes")

    etu = pd.read_sql("SELECT * FROM etudiant", conn)
    mat = pd.read_sql("SELECT * FROM matiere", conn)

    etu_id = st.selectbox("Étudiant", etu["id"],
        format_func=lambda x: etu.loc[etu["id"]==x, "nom"].values[0])

    mat_id = st.selectbox("Matière", mat["id"],
        format_func=lambda x: mat.loc[mat["id"]==x, "design"].values[0])

    note = st.number_input("Note", 0.0, 20.0)

    if st.button("Ajouter note"):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO note(etudiant_id, matiere_id, note) VALUES (%s,%s,%s)",
                        (etu_id, mat_id, note))
            
            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("INSERT", username))

            conn.commit()
        st.success("Ajoutée")

    df = pd.read_sql("""
        SELECT n.id, e.nom, m.design, n.note
        FROM note n
        JOIN etudiant e ON e.id=n.etudiant_id
        JOIN matiere m ON m.id=n.matiere_id
    """, conn)

    st.dataframe(df)

# =========================
# AUDIT
# =========================
elif menu == "Audit":

    if role != "admin":
        st.error("Accès refusé")
        st.stop()

    st.header(" Audit")

    # =========================
    # TABLE AUDIT
    # =========================
    df = pd.read_sql("""
        SELECT 
            id,
            operation,
            date_op,
            utilisateur,
            etudiant_id,
            matiere_id,
            note_ancien,
            note_nouv
        FROM audit_note
        ORDER BY date_op DESC
    """, conn)

    # Renommer colonnes (plus lisible)
    df = df.rename(columns={
        "id": "ID",
        "operation": "Opération",
        "date_op": "Date",
        "utilisateur": "Utilisateur",
        "etudiant_id": "ID Étudiant",
        "matiere_id": "ID Matière",
        "note_ancien": "Ancienne note",
        "note_nouv": "Nouvelle note"
    })

    st.subheader(" Historique des actions")
    st.dataframe(df, use_container_width=True)

    # =========================
    # STATISTIQUES
    # =========================
    st.subheader(" Statistiques")

    stats = pd.read_sql("""
        SELECT
            COUNT(*) FILTER (WHERE operation='INSERT') AS insertions,
            COUNT(*) FILTER (WHERE operation='UPDATE') AS modifications,
            COUNT(*) FILTER (WHERE operation='DELETE') AS suppressions
        FROM audit_note
    """, conn)

    col1, col2, col3 = st.columns(3)

    col1.success(f"Ajouts : {stats['insertions'][0]}")
    col2.info(f"Modifications : {stats['modifications'][0]}")
    col3.error(f"Suppressions : {stats['suppressions'][0]}")

    # =========================
    # STATS PAR UTILISATEUR
    # =========================
    st.subheader("Activité par utilisateur")

    user_stats = pd.read_sql("""
        SELECT utilisateur, COUNT(*) as total_actions
        FROM audit_note
        GROUP BY utilisateur
        ORDER BY total_actions DESC
    """, conn)

    st.dataframe(user_stats, use_container_width=True)