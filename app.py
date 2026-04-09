import streamlit as st
import pandas as pd
from db import get_connection
from supabase import create_client

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Gestion Notes Pro", layout="wide")

conn = get_connection()

# =========================
# SUPABASE
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
                st.rerun()
            else:
                st.error("Email ou mot de passe incorrect")

        except Exception as e:
            st.error(str(e))

    st.stop()

# =========================
# USER INFO (role + username)
# =========================
def get_user_info(user_id):
    res = supabase.table("profiles").select("role, username").eq("id", user_id).execute()
    if res.data:
        return res.data[0]["role"], res.data[0]["username"]
    return "user", "user"

role, username = get_user_info(st.session_state.user.id)

# =========================
# SIDEBAR
# =========================
st.sidebar.write(f"👤 {username} ({role})")

if st.sidebar.button("Déconnexion"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

st.title("Gestion des Notes")

# =========================
# MENU
# =========================
if role == "admin":
    menu = st.sidebar.radio("Menu", ["Audit"])
else:
    menu = st.sidebar.radio("Menu", ["Étudiants", "Matières", "Notes"])


# =========================
# ETUDIANTS
# =========================
if menu == "Étudiants":

    nom = st.text_input("Nom étudiant")

    if st.button("Ajouter étudiant"):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO etudiant(nom) VALUES (%s)", (nom,))

            #  AUDIT avec utilisateur connecté
            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("INSERT", username))

            conn.commit()

        st.success(f"{username} a ajouté un étudiant")

    df = pd.read_sql("SELECT * FROM etudiant", conn)
    st.dataframe(df)

# =========================
# MATIERES
# =========================
elif menu == "Matières":

    design = st.text_input("Nom matière")

    if st.button("Ajouter matière"):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO matiere(design) VALUES (%s)", (design,))

            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("INSERT", username))

            conn.commit()

        st.success(f"{username} a ajouté une matière")

# =========================
# NOTES
# =========================
elif menu == "Notes":

    etu = pd.read_sql("SELECT * FROM etudiant", conn)
    mat = pd.read_sql("SELECT * FROM matiere", conn)

    etu_id = st.selectbox("Étudiant", etu["id"],
        format_func=lambda x: etu.loc[etu["id"]==x, "nom"].values[0])

    mat_id = st.selectbox("Matière", mat["id"],
        format_func=lambda x: mat.loc[mat["id"]==x, "design"].values[0])

    note = st.number_input("Note", 0.0, 20.0)

    if st.button("Ajouter note"):
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO note(etudiant_id, matiere_id, note)
                VALUES (%s,%s,%s)
            """, (etu_id, mat_id, note))

            cur.execute("""
                INSERT INTO audit_note(operation, utilisateur, date_op)
                VALUES (%s, %s, NOW())
            """, ("INSERT", username))

            conn.commit()

        st.success(f"{username} a ajouté une note")

# =========================
# AUDIT
# =========================
elif menu == "Audit":

    if role != "admin":
        st.error("Accès refusé")
        st.stop()

    st.header("Audit")

    df = pd.read_sql("""
        SELECT operation, utilisateur, date_op
        FROM audit_note
        ORDER BY date_op DESC
    """, conn)

    df = df.rename(columns={
        "operation": "Opération",
        "utilisateur": "Utilisateur",
        "date_op": "Date"
    })

    st.dataframe(df)

    # =========================
    # STATS
    # =========================
    st.subheader("Statistiques")

    stats = pd.read_sql("""
        SELECT
            COUNT(*) FILTER (WHERE operation='INSERT') AS insertions,
            COUNT(*) FILTER (WHERE operation='UPDATE') AS updates,
            COUNT(*) FILTER (WHERE operation='DELETE') AS deletes
        FROM audit_note
    """, conn)

    col1, col2, col3 = st.columns(3)
    col1.success(f"Ajouts : {stats['insertions'][0]}")
    col2.info(f"Modifications : {stats['updates'][0]}")
    col3.error(f"Suppressions : {stats['deletes'][0]}")