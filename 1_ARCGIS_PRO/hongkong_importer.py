"""
Hong Kong Emergency Services Data Importer
Imports hospitals, fire stations, and police stations from ArcGIS Living Atlas
"""

import requests
import psycopg2
from psycopg2.extras import execute_values
import secrets
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# LOAD ENVIRONMENT VARIABLES (SAFELY)
# ============================================================================
load_dotenv()

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'database': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD")
}

DEFAULT_PASSWORD_HASH = os.getenv("DEFAULT_PASSWORD_HASH")

# ============================================================================
# ARC GIS SOURCES (PUBLIC - SAFE)
# ============================================================================
HONG_KONG_URLS = {
    'hospital': {
        'url': 'https://services3.arcgis.com/6j1KwZfY2fZrfNMR/ArcGIS/rest/services/Hospitals_under_the_Hospital_Authority/FeatureServer/0',
        'name_field': 'NAME_EN',
        'address_field': 'ADDRESS_EN',
        'phone_field': 'NSEARCH01_EN'
    },
    'fire_station': {
        'url': 'https://services3.arcgis.com/6j1KwZfY2fZrfNMR/ArcGIS/rest/services/Fire_Stations_in_Hong_Kong/FeatureServer/0',
        'name_field': 'Name_ENG',
        'address_field': 'Address_ENG',
        'phone_field': 'Telephone'
    },
    'police_station': {
        'url': 'https://services3.arcgis.com/6j1KwZfY2fZrfNMR/ArcGIS/rest/services/Police_Stations_in_Hong_Kong/FeatureServer/0',
        'name_field': 'Facility_Name',
        'address_field': 'Address',
        'phone_field': 'Telephone'
    }
}

# ============================================================================
# FUNCTIONS
# ============================================================================

def test_url(url):
    """
    Test if ArcGIS URL is accessible and return field names
    """
    print(f"\n🔍 Testing URL: {url}")
    
    try:
        params = {'f': 'json'}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        metadata = response.json()
        
        if 'error' in metadata:
            print(f"❌ Error: {metadata['error']}")
            return None
        
        if 'fields' in metadata:
            print("✅ Service accessible!")
            print("\n📋 Available fields:")
            for field in metadata['fields']:
                print(f"   - {field['name']} ({field['type']})")
            return metadata['fields']
        else:
            print("⚠️ No field information found")
            return []
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def fetch_features(url, where_clause='1=1', max_records=1000):
    """
    Fetch features from ArcGIS REST API
    """
    query_url = f"{url}/query"
    
    params = {
        'where': where_clause,
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'resultRecordCount': max_records
    }
    
    print("\n📡 Fetching data...")
    
    try:
        response = requests.get(query_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            print(f"❌ Error: {data['error']}")
            return []
        
        if 'features' in data:
            print(f"✅ Retrieved {len(data['features'])} features")
            return data['features']
        else:
            print("⚠️ No features found")
            return []
            
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return []


def parse_feature(feature, service_type, config):
    """
    Parse ArcGIS feature into database format
    """
    attrs = feature.get('attributes', {})
    geom = feature.get('geometry', {})
    
    # Extract coordinates
    if 'x' in geom and 'y' in geom:
        longitude = geom['x']
        latitude = geom['y']
    elif 'rings' in geom and len(geom['rings']) > 0:
        longitude = geom['rings'][0][0][0]
        latitude = geom['rings'][0][0][1]
    elif 'paths' in geom and len(geom['paths']) > 0:
        longitude = geom['paths'][0][0][0]
        latitude = geom['paths'][0][0][1]
    else:
        print("⚠️ No valid geometry found")
        return None
    
    # Convert Web Mercator if required
    if abs(longitude) > 180 or abs(latitude) > 90:
        import math
        longitude = longitude / 20037508.34 * 180
        latitude = math.atan(math.exp(latitude / 20037508.34 * math.pi)) * 360 / math.pi - 90
    
    name = attrs.get(config['name_field'], f"Unknown {service_type}")
    address = attrs.get(config['address_field'])
    phone = attrs.get(config['phone_field'])
    
    service_id = f"{service_type[:3].upper()}-{secrets.token_hex(4).upper()}"
    
    return {
        'service_id': service_id,
        'service_name': str(name)[:255],
        'service_type': service_type,
        'latitude': latitude,
        'longitude': longitude,
        'address': str(address)[:255] if address else None,
        'contact_phone': str(phone)[:50] if phone else None,
        'available_units': 5
    }


def import_to_database(services_data, clear_existing=True):
    """
    Import services to PostgreSQL database
    """
    if not services_data:
        print("⚠️ No data to import!")
        return
    
    print(f"\n📥 Importing {len(services_data)} services to database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        if clear_existing:
            print("🗑️ Clearing existing services...")
            cur.execute("DELETE FROM service_providers")
        
        values = []
        email_counter = 1
        
        for service in services_data:
            unique_email = f"service{email_counter}@example.com"
            email_counter += 1
            
            values.append((
                service['service_id'],
                unique_email,
                service['service_name'],
                service['service_type'],
                service['latitude'],
                service['longitude'],
                service['address'],
                service['contact_phone'],
                service['available_units'],
                DEFAULT_PASSWORD_HASH,
                service['longitude'],
                service['latitude']
            ))
        
        insert_query = """
            INSERT INTO service_providers 
            (service_id, email, service_name, service_type, latitude, longitude, 
             address, contact_phone, available_units, password_hash, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT (service_id) DO NOTHING
        """
        
        inserted_count = 0
        
        for val in values:
            try:
                cur.execute(insert_query, val)
                inserted_count += 1
            except Exception as e:
                conn.rollback()
                print(f"⚠️ Skipped {val[2]}: {str(e)[:80]}")
                conn = psycopg2.connect(**DB_CONFIG)
                cur = conn.cursor()
        
        conn.commit()
        
        print(f"✅ Successfully imported {inserted_count} services!")
        
        print("\n📊 Summary by type:")
        cur.execute("""
            SELECT service_type, COUNT(*) 
            FROM service_providers 
            GROUP BY service_type
            ORDER BY service_type
        """)
        
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]} services")
        
        print("\n📋 Sample records:")
        cur.execute("""
            SELECT service_name, service_type, latitude, longitude, address
            FROM service_providers 
            LIMIT 5
        """)
        
        for row in cur.fetchall():
            print(f"   - {row[0]} ({row[1]})")
            print(f"     Location: {row[2]:.4f}, {row[3]:.4f}")
            if row[4]:
                print(f"     Address: {row[4][:50]}...")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")


def main():
    """
    Main function
    """
    print("=" * 70)
    print("🇭🇰 HONG KONG EMERGENCY SERVICES DATA IMPORTER")
    print("   Source: ArcGIS Living Atlas")
    print("=" * 70)
    
    # Test DB
    print("\n📌 STEP 1: Testing database connection...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    print("\n📌 STEP 2: Fetching data from ArcGIS Living Atlas...")
    
    all_services = []
    
    for service_type, config in HONG_KONG_URLS.items():
        print(f"\n{'='*70}")
        print(f"Processing: {service_type.upper()}")
        print('='*70)
        
        fields = test_url(config['url'])
        if fields is None:
            print(f"⚠️ Skipping {service_type}")
            continue
        
        features = fetch_features(config['url'])
        if not features:
            continue
        
        for feature in features:
            parsed = parse_feature(feature, service_type, config)
            if parsed:
                all_services.append(parsed)
        
        print(f"✅ Parsed {len(features)} {service_type} records")
    
    if all_services:
        print("\n📌 STEP 3: Importing to database")
        import_to_database(all_services, clear_existing=True)
        print("\n✅ IMPORT COMPLETE!")
    else:
        print("\n❌ NO DATA IMPORTED")


if __name__ == "__main__":
    main()
