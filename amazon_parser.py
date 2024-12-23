from bs4 import BeautifulSoup
import pymongo
import re

def connect_to_mongodb():
    """Establish connections to both source and destination databases"""
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    source_db = client["raw_laptop_data"]
    dest_db = client["laptop_data"]
    return source_db, dest_db

def extract_title(soup):
    """Extract product title"""
    title_element = soup.find('span', {'id': 'productTitle'})
    if title_element:
        return title_element.text.strip()
    return None

def extract_price_info(soup):
    """Extract current price, MRP and savings percentage"""
    price_info = {
        "current_price": None,
        "mrp": None,
        "discount_percentage": None
    }
    
    # Extract current price
    price_element = soup.find('span', {'class': 'a-price-whole'})
    if price_element:
        price_info["current_price"] = price_element.text.strip().replace(',', '')
    
    # Extract MRP (original price)
    mrp_element = soup.find('span', {'class': 'a-price a-text-price'})
    if mrp_element:
        mrp_text = mrp_element.find('span', {'class': 'a-offscreen'})
        if mrp_text:
            mrp = mrp_text.text.strip().replace('₹', '').replace(',', '')
            price_info["mrp"] = mrp
    
    # Extract discount percentage
    discount_element = soup.find('span', {'class': 'savingPriceOverride'})
    if discount_element:
        discount = discount_element.text.strip().replace('-', '').replace('%', '')
        price_info["discount_percentage"] = discount
    
    return price_info

def parse_technical_details(html_content):
    """Extract and parse technical details from the HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    tech_details = {}
    
    # Look for the product details table
    table = soup.find('table', {'id': 'productDetails_techSpec_section_1'})
    if table:
        rows = table.find_all('tr')
        for row in rows:
            label = row.find('th')
            value = row.find('td')
            if label and value:
                key = label.text.strip().replace('\u200e', '').strip()
                val = value.text.strip().replace('\u200e', '').strip()
                tech_details[key] = val

    return tech_details

def standardize_specs(tech_details):
    """Standardize and organize technical specifications"""
    organized_specs = {
        "brand": tech_details.get("Brand"),
        "model": tech_details.get("Item model number"),
        "series": tech_details.get("Series"),
        "processor": {
            "brand": tech_details.get("Processor Brand"),
            "type": tech_details.get("Processor Type"),
            "speed": tech_details.get("Processor Speed"),
            "cores": tech_details.get("Processor Count")
        },
        "memory": {
            "ram_size": tech_details.get("RAM Size"),
            "technology": tech_details.get("Memory Technology"),
            "max_supported": tech_details.get("Maximum Memory Supported")
        },
        "storage": {
            "size": tech_details.get("Hard Drive Size"),
            "type": tech_details.get("Hard Disk Description"),
            "interface": tech_details.get("Hard Drive Interface")
        },
        "display": {
            "size": tech_details.get("Standing screen display size"),
            "resolution": tech_details.get("Screen Resolution")
        },
        "graphics": {
            "brand": tech_details.get("Graphics Chipset Brand"),
            "type": tech_details.get("Graphics Card Description"),
            "memory_type": tech_details.get("Graphics RAM Type")
        },
        "operating_system": tech_details.get("Operating System"),
        "battery": {
            "life": tech_details.get("Average Battery Life (in hours)"),
            "standby_life": tech_details.get("Average Battery Standby Life (in hours)"),
            "cells": tech_details.get("Number of Lithium Ion Cells"),
            "energy_content": tech_details.get("Lithium Battery Energy Content")
        },
        "physical": {
            "dimensions": tech_details.get("Product Dimensions"),
            "weight": tech_details.get("Item Weight"),
            "color": tech_details.get("Colour")
        },
        "connectivity": {
            "type": tech_details.get("Connectivity Type"),
            "usb2_ports": tech_details.get("Number of USB 2.0 Ports"),
            "usb3_ports": tech_details.get("Number of USB 3.0 Ports")
        },
        "included_components": tech_details.get("Included Components")
    }
    
    return organized_specs

def process_html_documents():
    """Main function to process HTML documents and organize data"""
    source_db, dest_db = connect_to_mongodb()
    
    # Get collections
    raw_collection = source_db["raw_pages"]
    laptop_collection = dest_db["laptop_specs"]
    
    # Drop existing collection to start fresh
    laptop_collection.drop()
    print("Dropped existing collection")
    
    # Process each HTML document
    for doc in raw_collection.find():
        try:
            # Get HTML content from the document
            html_content = doc.get('content', doc.get('html_content', doc.get('source', doc.get('html'))))
            
            if not html_content:
                print(f"Could not find HTML content in document {doc['_id']}")
                continue
            
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title and price information
            title = extract_title(soup)
            price_info = extract_price_info(soup)
            
            # Extract and organize specifications
            tech_details = parse_technical_details(html_content)
            organized_specs = standardize_specs(tech_details)
            
            # Create document for laptop_data database
            laptop_doc = {
                "source_id": doc["_id"],
                "url": doc.get("url", ""),  # Get URL from raw pages
                "title": title,
                "pricing": {
                    "current_price": price_info["current_price"],
                    "mrp": price_info["mrp"],
                    "discount_percentage": price_info["discount_percentage"]
                },
                "specifications": organized_specs,
                "raw_specs": tech_details
            }
            
            # Insert into laptop_data collection
            laptop_collection.insert_one(laptop_doc)
            print(f"Successfully processed document {doc['_id']}")
            
        except Exception as e:
            print(f"Error processing document {doc['_id']}: {str(e)}")

if __name__ == "__main__":
    process_html_documents()