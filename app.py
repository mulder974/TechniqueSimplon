# streamlit/app.py

import os
import pandas as pd
import streamlit as st
import requests
import plotly.express as px

# Set page config and style
st.set_page_config(
    page_title="Dashboard des Ventes",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stExpander {
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🛍️ Configuration")
    
    # File upload section
    st.subheader("📤 Import des données")
    uploaded_file = st.file_uploader("Importer un fichier CSV", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if st.button("📥 Charger dans la base", type="primary"):
            # Define expected columns for each table
            table_columns = {
                'sells': ["Date", "ID Référence produit", "Quantité", "ID Magasin"],
                'products': ["ID Référence produit", "Prix"],
                'shops': ["ID Magasin", "Ville"]
            }
            
            # Determine table name based on columns present in uploaded file
            table_name = None
            for table, expected_cols in table_columns.items():
                if all(col in df.columns for col in expected_cols):
                    table_name = table
                    break
                    
            if table_name is None:
                st.error("❌ Le format du fichier ne correspond à aucune table")
            else:
                data_json = df.to_dict(orient='records')
                response = requests.post("http://127.0.0.1:5000/upload-csv",
                                      json={"data": data_json, "table_name": table_name})
            if response.status_code == 200:
                st.success("✅ Données importées avec succès!")
            else:
                st.error(f"❌ Erreur: {response.json().get('error')}")
    
    # Filter selection
    st.subheader("📊 Type d'analyse")
    filter_option = st.radio("", ("Volume", "Valeur"), 
                           format_func=lambda x: f"Analyse en {x.lower()}")

# Main content
st.title("📈 Dashboard des Ventes")

# Preview of uploaded data
if uploaded_file is not None:
    with st.expander("🔍 Aperçu des données importées"):
        st.dataframe(df, use_container_width=True)

# Create three columns for key metrics
col1, col2, col3 = st.columns(3)

# Total revenue/volume
with col1:
    if filter_option == "Volume":
        response = requests.get("http://127.0.0.1:5000/sellsbyshop")
        data = response.json()
        df_sells_by_shop = pd.DataFrame(data, columns=["town", "shop_id", "total_quantity"])
        total = df_sells_by_shop["total_quantity"].sum()
        st.metric("📦 Volume Total", f"{total:,.0f} unités")
    else:
        response = requests.get("http://127.0.0.1:5000/sellsvaluebyshop")
        data = response.json()
        df_sells_value_by_shop = pd.DataFrame(data, columns=["town", "shop_id", "total_value"])
        df_sells_value_by_shop['total_value'] = pd.to_numeric(df_sells_value_by_shop['total_value'], errors='coerce')
        total = df_sells_value_by_shop["total_value"].sum().round(2)
        st.metric("💶 Chiffre d'Affaires Total", f"{total} €")

# Products analysis
tab1, tab2, tab3 = st.tabs(["📊 Analyse par Produit", "🏪 Analyse par Magasin", "📈 Répartition par Taille"])

with tab1:
    if filter_option == "Volume":
        response = requests.get("http://127.0.0.1:5000/sellsbyproduct")
        data = response.json()
        df_sells_by_product = pd.DataFrame(data, columns=["product_reference", "total_quantity"])
        
        st.subheader("Ventes par produit (Volume)")
        chart_col, table_col = st.columns([2, 1])
        
        with chart_col:
            st.bar_chart(df_sells_by_product.set_index("product_reference")["total_quantity"])
        
        with table_col:
            st.dataframe(df_sells_by_product.style.highlight_max(["total_quantity"]), 
                        use_container_width=True)
    else:
        response = requests.get("http://127.0.0.1:5000/sellsvaluebyproduct")
        data = response.json()
        df_sells_value_by_product = pd.DataFrame(data, columns=["product_reference", "total_value"])
        df_sells_value_by_product['total_value'] = pd.to_numeric(df_sells_value_by_product['total_value'], 
                                                               errors='coerce')
        
        st.subheader("Ventes par produit (Valeur)")
        chart_col, table_col = st.columns([2, 1])
        
        with chart_col:
            st.bar_chart(df_sells_value_by_product.set_index("product_reference")["total_value"])
        
        with table_col:
            st.dataframe(df_sells_value_by_product.style.highlight_max(["total_value"]), 
                        use_container_width=True)

with tab2:
    if filter_option == "Volume":
        response = requests.get("http://127.0.0.1:5000/sellsbyshopbyproduct")
        data = response.json()
        df = pd.DataFrame(data, columns=["town", "shop_id", "product_reference", "total_quantity"])
        
        st.subheader("Détails par magasin (Volume)")
        for town in df['town'].unique():
            with st.expander(f"🏪 {town}"):
                town_data = df[df['town'] == town]
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.bar_chart(town_data.set_index("product_reference")["total_quantity"])
                
                with col2:
                    total = town_data['total_quantity'].sum()
                    st.metric("Volume Total", f"{total:,.0f} unités")
                    st.dataframe(town_data, use_container_width=True)
    else:
        response = requests.get("http://127.0.0.1:5000/sellsvaluebyshopbyproduct")
        data = response.json()
        df = pd.DataFrame(data, columns=["town", "shop_id", "product_reference", "total_value"])
        df['total_value'] = pd.to_numeric(df['total_value'], errors='coerce')
        
        st.subheader("Détails par magasin (Valeur)")
        for town in df['town'].unique():
            with st.expander(f"🏪 {town}"):
                town_data = df[df['town'] == town]
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.bar_chart(town_data.set_index("product_reference")["total_value"])
                
                with col2:
                    total = town_data['total_value'].sum().round(2)
                    st.metric("Chiffre d'Affaires", f"{total:,.2f} €")
                    st.dataframe(town_data, use_container_width=True)

with tab3:
    st.subheader("Répartition par Taille")
    if filter_option == "Volume":
        # Pie chart for volume distribution by product
        response = requests.get("http://127.0.0.1:5000/sellsbyproduct")
        data = response.json()
        df_sells_by_product = pd.DataFrame(data, columns=["product_reference", "total_quantity"])
        st.write("Répartition du volume par produit")
        fig = px.pie(df_sells_by_product, names='product_reference', values='total_quantity', title='Volume par Produit')
        st.plotly_chart(fig)
        
        # Pie chart for volume distribution by shop
        response = requests.get("http://127.0.0.1:5000/sellsbyshop")
        data = response.json()
        df_sells_by_shop = pd.DataFrame(data, columns=["town", "shop_id", "total_quantity"])
        st.write("Répartition du volume par magasin")
        fig = px.pie(df_sells_by_shop, names='town', values='total_quantity', title='Volume par Magasin')
        st.plotly_chart(fig)
    else:
        # Pie chart for value distribution by product
        response = requests.get("http://127.0.0.1:5000/sellsvaluebyproduct")
        data = response.json()
        df_sells_value_by_product = pd.DataFrame(data, columns=["product_reference", "total_value"])
        df_sells_value_by_product['total_value'] = pd.to_numeric(df_sells_value_by_product['total_value'], errors='coerce')
        st.write("Répartition de la valeur par produit")
        fig = px.pie(df_sells_value_by_product, names='product_reference', values='total_value', title='Valeur par Produit')
        st.plotly_chart(fig)
        
        # Pie chart for value distribution by shop
        response = requests.get("http://127.0.0.1:5000/sellsvaluebyshop")
        data = response.json()
        df_sells_value_by_shop = pd.DataFrame(data, columns=["town", "shop_id", "total_value"])
        df_sells_value_by_shop['total_value'] = pd.to_numeric(df_sells_value_by_shop['total_value'], errors='coerce')
        st.write("Répartition de la valeur par magasin")
        fig = px.pie(df_sells_value_by_shop, names='town', values='total_value', title='Valeur par Magasin')
        st.plotly_chart(fig)

