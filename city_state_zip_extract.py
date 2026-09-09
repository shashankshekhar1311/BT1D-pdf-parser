import pandas as pd
# Download complete open-source US ZIP dataset
raw_url = "https://raw.githubusercontent.com/akinniyi/US-Zip-Codes-With-City-State/master/uszips.csv"
df = pd.read_csv(raw_url, dtype={'zip': str})
# Format 5-digit ZIP codes (preserving leading zeros) and clean columns
df['zip_code'] = df['zip'].astype(str).str.zfill(5)
df['city'] = df['city'].astype(str).str.replace("'", "''")  # Escape single quotes for SQL
df['state_code'] = df['state_id']
# Select target columns
clean_df = df[['zip_code', 'city', 'state_code']].drop_duplicates(subset=['zip_code'])
# 1. Save Clean CSV for Redshift COPY command
clean_df.to_csv('ref_zip_codes_full.csv', index=False)
print("Saved ref_zip_codes_full.csv (41,000+ rows)")
# 2. Save full SQL INSERT script
with open('ref_zip_codes_full.sql', 'w') as f:
   f.write("INSERT INTO ref_zip_codes (zip_code, city, state_code) VALUES\n")
   values = [f"('{row.zip_code}', '{row.city}', '{row.state_code}')" for _, row in clean_df.iterrows()]
   f.write(",\n".join(values) + ";\n")
print("Saved ref_zip_codes_full.sql")