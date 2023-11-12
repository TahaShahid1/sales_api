import uvicorn
from datetime import datetime, date

from fastapi import FastAPI, HTTPException, Query
from fastapi.params import Depends
from sqlalchemy.orm import Session, joinedload

from constants import LOW_STOCK_LIMIT, TIME_INTERVAL_MAPPING
from utils.common_utils import generate_rand
from db_utils import get_db, Inventory, InventoryStatus, Category, Product, Sale

app = FastAPI()


##############################
### Inventory related views ###
##############################

@app.get('/inventory/status')
async def get_inventory_status(db: Session = Depends(get_db)) -> dict:
    """
    Fetches inventory current status
    :return: dict
    """
    try:
        # Fetch inventory data
        inventory_data = db.query(Inventory).all()

        # Format inventory data
        inventory_data = [{'product_name': i.product.product_name,
                           'stock': i.stock, 'low_stock': True if i.stock < LOW_STOCK_LIMIT else False}
                          for i in inventory_data]
        return {
            'status': 'success',
            'inventory_data': inventory_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/inventory/add')
async def add_inventory(product_sku: str, stock: int = 0, db: Session = Depends(get_db)):
    """
    Adds Item to inventory
    :param product_id: product_id
    :param stock: stock (units of item)
    :param db: DB session object
    :return:
    """
    try:
        # Check if product sku or stock is missing in request
        if not product_sku or not stock:
            return {
                'status': 'failed',
                'message': 'product id and stock are required'
            }
        # product = db.query(Inventory).join(Inventory.product).filter(Product.sku == product_sku).first()

        # Check if product is deleted
        product = db.query(Product).filter(Product.sku == product_sku).first()
        if not product:
            return {
                'status': 'failed',
                'message': 'Product not found'
            }

        # db.query(Inventory).filter(Inventory.product_id == product.id).update({'stock': Inventory.stock + stock})

        # Fetch product entry in inventory
        inventory_product = db.query(Inventory).filter(Inventory.product_id == product.id).first()

        # Add if product is not listed in inventory else add items in stock
        if not inventory_product:
            db.add(Inventory(**{'product_id': product.id, 'stock': stock}))
        else:
            inventory_product.stock += stock
            inventory_update = InventoryStatus(**{'product_id': product.id, 'operation': 'add', 'pieces': stock})
            db.add(inventory_update)

        # Save in db
        db.commit()

        return {
            "status": "success",
            "message": "Inventory item stock added successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inventory/track")
def get_inventory_track_within_date_range(
        start_date: date = Query(..., title="Start Date", description="Start date of the range"),
        end_date: date = Query(..., title="End Date", description="End date of the range"),
        db: Session = Depends(get_db)):
    """
    Returns Inventory changes by date
    :param start_date: Start Date filter
    :param end_date: End Date filter
    :param db: DB session
    :return:
    """
    try:
        # Get data of past 7 days if range is not defined
        if not start_date and end_date:
            start_date = datetime.today() - datetime.timedelta(days=7)
            end_date = datetime.today()

        # Fetch inventory data within the given time range
        inventory_track_data = (
            db.query(InventoryStatus)
            .filter(InventoryStatus.operation_date >= start_date, InventoryStatus.operation_date <= end_date)
            .all()
        )

        # Format and return data
        inventory_track_data = [{
            'product_name': i.product.product_name,
            'product_sku': i.product.sku,
            'units': i.pieces,
            'operation': i.operation,
            'operation_date': i.operation_date
        } for i in inventory_track_data]

        return {
            "status": "success",
            "data": inventory_track_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#################################
# Product/Category related views #
#################################

@app.get('/category/list')
async def get_categories(db: Session = Depends(get_db)):
    """
    return available categories
    :return:
    """
    try:
        # list categories, Format and return
        categories = db.query(Category).all()
        categories = [{
            'name': i.cat_name,
            'description': i.cat_description
        } for i in categories]

        return {
            'status': 'success',
            'data': categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/category/add')
async def add_categories(name: str, description: str = '', db: Session = Depends(get_db)):
    """
    return available categories
    :return:
    """
    try:
        # Check if name param is missing
        if not name:
            return {
                'status': 'failed',
                'message': 'no name was provided'
            }
        # Check if category is already in db
        if db.query(Category).filter(Category.cat_name == name).first():
            return {
                'status': 'failed',
                'message': 'Category already present'
            }

        # Add entry in db
        category = Category(**{'cat_name': name, 'cat_description': description})
        db.add(category)

        db.commit()

        return {
            'status': 'success',
            'message': 'category added'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/product/list')
async def get_products(db: Session = Depends(get_db)):
    """
    return available categories
    :return:
    """
    try:
        # List products and return formatted data
        products = db.query(Product).all()
        products = [{
            'name': i.product_name,
            'sku': i.sku,
            'price': i.price
        } for i in products]

        return {
            'status': 'success',
            'data': products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/product/add')
async def add_product(name: str, price: float, category: str, sku: str = '', db: Session = Depends(get_db)):
    """
    return available products
    :return:
    """
    try:
        # Check for missing params in request
        if not name or not price or not category:
            return {
                'status': 'failed',
                'message': 'No name/price/category was provided'
            }

        # Generate unique SKU if not in request
        if not sku:
            sku = generate_rand()

        # Check if given category is not in system
        category = db.query(Category).filter(Category.cat_name == category).first()
        if not category:
            return {
                'status': 'failed',
                'message': 'No category Found'
            }

        # Check if product is alread present in system
        if db.query(Product).filter(Product.sku == sku).first():
            return {
                'status': 'failed',
                'message': 'Product already present'
            }

        # Add product to system
        product = Product(**{'product_name': name, 'sku': sku, 'price': price, 'category_id': category.id})
        db.add(product)

        db.commit()

        return {
            'status': 'success',
            'message': 'Product added'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.delete('/product/delete/')
# async def delete_product(sku: str, db: Session = Depends(get_db)):
#     """
#     Delete a product
#     :param sku: Product sku
#     :param db: DB Session
#     :return:
#     """
#     try:
#         product = db.query(Product).filter(Product.sku == sku).first()
#         if not product:
#             return {
#                 'status': 'failed',
#                 'message': 'No sku found'
#             }
#
#         product.is_deleted = True
#
#         db.commit()
#         return {
#             'status': 'success',
#             'message': 'Product deleted'
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


##############################
#### Sales related views ####
##############################


@app.post('/sale/make_sale')
async def sale_product(product_sku: str, quantity: int = 1, db: Session = Depends(get_db)):
    """
    Sale a product
    :param product_sku: sold product sku
    :param quantity: product quantity sold
    :param db: DB Session Instance
    :return:
    """
    try:
        # Check for request required params
        if not product_sku:
            return {
                'status': 'failed',
                'message': 'No product sku given'
            }

        # Fetch product from db
        product = db.query(Product).filter(Product.sku == product_sku).first()
        if not product:
            return {
                'status': 'failed',
                'message': 'No product was found'
            }

        # Fetch inventory entry for product
        inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()

        # Check if stock is lesser than purchased quantity
        if inventory.stock < quantity:
            return {
                'status': 'failed',
                'message': 'Not enough items in stock'
            }

        # reset stock after sale
        inventory.stock -= quantity

        # Update transaction details to inventory status
        inventory_status = InventoryStatus(**{
            'product_id': product.id,
            'operation': 'remove',
            'pieces': quantity
        })
        db.add(inventory_status)

        # Add record to sales table
        sales = Sale(**{
            'product_id': product.id,
            'price_per_piece': product.price,
            'pieces': quantity
        })
        db.add(sales)

        db.commit()

        return {
            'status': 'success',
            'message': 'Product sold',
            'reciept_data': {
                'item': product.product_name,
                'unit': quantity,
                'price': product.price,
                'total': product.price * quantity
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/sales/get_data')
async def get_sales_data(db: Session = Depends(get_db),
                         start_date: date = Query(..., title="Start Date", description="Start date of the range"),
                         end_date: date = Query(..., title="End Date", description="End date of the range"),
                         product_sku: str = '', category: str = ''):
    """
    Returns Sales Data from given time frame
    :param db: DB connection Session
    :param start_date: Starting date
    :param end_date: Ending Date
    :param product_id: Product name/SKU
    :param category: Product Category
    :return: Dict
    """
    try:
        # Sales data if product and category are not defined
        if not product_sku and not category:
            sales_data = db.query(Sale).filter(Sale.sale_time >= start_date, Sale.sale_time <= end_date)

        # Sales data if product is not defined but category is given
        elif not product_sku and category:
            sales_data = (
                db.query(Sale)
                .join(Product)
                .join(Category)
                .filter(Category.cat_name.in_([category]), Sale.sale_time >= start_date, Sale.sale_time <= end_date)
                .options(joinedload(Sale.product).joinedload(Product.category))
                .all()
            )

        # Sales data if category is not defined but product is given
        elif not category and product_sku:
            sales_data = (
                db.query(Sale)
                .join(Product)
                .filter(Product.sku.in_([product_sku]), Sale.sale_time >= start_date, Sale.sale_time <= end_date)
                .all()
            )

        # Sales data if product and category are given
        else:
            sales_data = (
                db.query(Sale)
                .join(Product)
                .join(Category)
                .filter(Category.cat_name.in_([category]), Product.sku.in_([product_sku]),
                        Sale.sale_time >= start_date, Sale.sale_time <= end_date)
                .options(joinedload(Sale.product).joinedload(Product.category))
                .all()
            )

        # Data Formatting
        sales_data = [{
            'invoice_no': i.id,
            'item': i.product.product_name,
            'quantity': i.pieces,
            'price per piece': i.price_per_piece,
            'total': i.pieces * i.price_per_piece,
            'invoice time': i.sale_time
        } for i in sales_data]

        return {
            'status': 'success',
            'data': sales_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/sales/get_timed_data')
async def get_timed_sales_data(interval: str, db: Session = Depends(get_db)):
    """
    Returns Fixed interval timed sales data points
    :param interval: time interval i.e. today, week, month, year
    :param db: DB Sessions Instance
    :return:
    """
    try:
        # Check for time interval parameter
        interval_timedelta = TIME_INTERVAL_MAPPING.get(interval.lower())
        if not interval_timedelta:
            return {
                'status': 'failed',
                'message': f'Interval value not defined. possible choices are: {",".join(TIME_INTERVAL_MAPPING.keys())}'
            }

        start_time = datetime.today() - interval_timedelta
        end_time = datetime.today()

        # Fetch data between time intervals
        sales_data = (db.query(Sale).filter(Sale.sale_time >= start_time, Sale.sale_time <= end_time).all())

        # Format data
        sales_data = [{
            'invoice_no': i.id,
            'item': i.product.product_name,
            'quantity': i.pieces,
            'price per piece': i.price_per_piece,
            'total': i.pieces * i.price_per_piece,
            'invoice time': i.sale_time
        } for i in sales_data]

        return {
            'status': 'success',
            'interval': interval,
            'data': sales_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/sales/compare_data')
async def compare_sales_data(db: Session = Depends(get_db),
                             start_date: date = Query(..., title="Start Date", description="Start date of the range"),
                             start_date2: date = Query(..., title="Start Date 2",
                                                       description="Start date of the range 2"),
                             end_date: date = Query(..., title="End Date", description="End date of the range"),
                             end_date2: date = Query(..., title="End Date 2", description="End date of the range 2"),
                             category1: str = '', category2: str = ''):
    """
    Returns Comparison of data points by period
    :param start_date: Start date for period 1
    :param start_date2: Start date for period 2
    :param end_date: End date for period 1
    :param end_date2: End date for period 2
    :param category1: Category for period 1
    :param category2: Category for period 2
    :param db: DB Sessions Instance
    :return:
    """
    try:
        # If categories for comparison are given
        if category1 and category2:
            # Check if both categories exists in system
            category = db.query(Category).filter(Category.cat_name.in_([category1, category2])).all()
            if len(category) != 2:
                return {
                    'status': 'failed',
                    'message': 'Category not found in system'
                }

            # sales data for category1 in time period1
            sales_data_1 = (
                db.query(Sale)
                .join(Product)
                .join(Category)
                .filter(Category.cat_name.in_([category1]), Sale.sale_time >= start_date, Sale.sale_time <= end_date)
                .options(joinedload(Sale.product).joinedload(Product.category))
                .all()
            )
            # sales data for category2 in time period2
            sales_data_2 = (
                db.query(Sale)
                .join(Product)
                .join(Category)
                .filter(Category.cat_name.in_([category2]), Sale.sale_time >= start_date2, Sale.sale_time <= end_date2)
                .options(joinedload(Sale.product).joinedload(Product.category))
                .all()
            )

        # Check if both categories are not given
        elif not category1 and not category2:
            sales_data_1 = (
                db.query(Sale).filter(Sale.sale_time >= start_date, Sale.sale_time <= end_date).all()
            )

            sales_data_2 = (
                db.query(Sale).filter(Sale.sale_time >= start_date2, Sale.sale_time <= end_date2).all()
            )
        # Any other case
        else:
            return {
                'status': 'failed',
                'message': 'Cant compare without category set'
            }

        return {
            'status': 'success',
            'category1': category1,
            'period1': [{
                    'invoice_no': i.id,
                    'item': i.product.product_name,
                    'quantity': i.pieces,
                    'price per piece': i.price_per_piece,
                    'total': i.pieces * i.price_per_piece,
                    'invoice time': i.sale_time
                } for i in sales_data_1],
            'category2': category2,
            'period2': [{
                    'invoice_no': i.id,
                    'item': i.product.product_name,
                    'quantity': i.pieces,
                    'price per piece': i.price_per_piece,
                    'total': i.pieces * i.price_per_piece,
                    'invoice time': i.sale_time
                } for i in sales_data_2]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
