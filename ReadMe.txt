
Requirements
1. Python 3.6+

Steps to configure the system

1. Setup the mysql database on system
2. Use queries in Datascript file to create tables and populate data
3. Install requirements using requirements.txt file by command: pip install -r requirements.txt
4. Configure database in utils>db_utils.py
4. run main.py to start app server on port 8000

Endpoint Description:

[/inventory/status]: list the items and quantity in inventory and gives low stock flag

[/inventory/add]: Add product in inventory

[/inventory/track]: returns transactions done in inventory in given time range

[/category/list]: list categories

[/category/add]: Add a category

[/product/list]: list available products in system

[/product/add]: Add product to system

[/sale/make_sale]: Sale an item of given quantity

[/sales/get_data]: Return sale data in given time range

[/sales/get_timed_data]: Return sale data in time intervals

[/sales/compare_data] Compare sale data of categories in given time intervals


DATABASE Tables:
NOTE: refer to DB_Schema.PNG for DB ERD

Category: contains product categories

Product: contains product data [joins with category]

Inventory: have inventory status and product stock [joins with product]

InventoryStatus: records transactions in inventory

Sales: records sales data of products [joins with product]
