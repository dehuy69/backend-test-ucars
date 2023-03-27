from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# Create SQLAlchemy engine and sessionmaker
SQLALCHEMY_DATABASE_URL = "'postgresql+psycopg2://user:password@hostname/ucars'"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for SQLAlchemy models
Base = declarative_base()


# Define CarBrand SQLAlchemy model
class CarBrand(Base):
    __tablename__ = "car_brands"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    logo = Column(String(50))
    description = Column(String(255))

    # Define relationship with CarModel
    car_models = relationship("CarModel", back_populates="car_brand")


# Define CarModel SQLAlchemy model
class CarModel(Base):
    __tablename__ = "car_models"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    car_brand_id = Column(Integer, ForeignKey("car_brands.id"))

    # Define relationship with CarBrand
    car_brand = relationship("CarBrand", back_populates="car_models")


# Create database tables
Base.metadata.create_all(bind=engine)


# Define Pydantic schemas for CarBrand and CarModel
class CarBrandBase(BaseModel):
    name: str
    logo: str = None
    description: str = None


class CarBrandCreate(CarBrandBase):
    pass


class CarBrandUpdate(CarBrandBase):
    pass


class CarBrand(CarBrandBase):
    id: int

    class Config:
        orm_mode = True


class CarModelBase(BaseModel):
    name: str
    car_brand_id: int


class CarModelCreate(CarModelBase):
    pass


class CarModelUpdate(CarModelBase):
    pass


class CarModel(CarModelBase):
    id: int

    class Config:
        orm_mode = True


# Create FastAPI app
app = FastAPI()


# Dependency for getting database session
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# Create CRUD endpoints for CarBrand
@app.post("/car_brands", response_model=CarBrand)
def create_car_brand(car_brand: CarBrandCreate, db: Session = Depends(get_db)):
    db_car_brand = CarBrand(name=car_brand.name, logo=car_brand.logo, description=car_brand.description)
    db.add(db_car_brand)
    db.commit()
    db.refresh(db_car_brand)
    return db_car_brand


@app.get("/car_brands/{car_brand_id}", response_model=CarBrand)
def read_car_brand(car_brand_id: int, db: Session = Depends(get_db)):
    db_car_brand = db.query(CarBrand).filter(CarBrand.id == car_brand_id).first()
    if db_car_brand is None:
        raise HTTPException(status_code=404, detail="Car brand not found")
    return db_car_brand


@app.put("/car_brands/{car_brand_id}", response_model=CarBrand)
def update_car_brand(car_brand_id: int, car_brand: CarBrandUpdate, db: Session = Depends(get_db)):
    db_car_brand = db.query(CarBrand).filter(CarBrand.id == car_brand_id).first()


    if db_car_brand is None:
        raise HTTPException(status_code=404, detail="Car brand not found")
    for field, value in car_brand:
        setattr(db_car_brand, field, value)
    db.commit()
    db.refresh(db_car_brand)
    return db_car_brand


@app.delete("/car_brands/{car_brand_id}")
def delete_car_brand(car_brand_id: int, db: Session = Depends(get_db)):

    db_car_brand = db.query(CarBrand).filter(CarBrand.id == car_brand_id).first()
    if db_car_brand is None:
        raise HTTPException(status_code=404, detail="Car brand not found")
    db.delete(db_car_brand)
    db.commit()
    return {"message": "Car brand deleted"}

@app.post("/car_models", response_model=CarModel)
def create_car_model(car_model: CarModelCreate, db: Session = Depends(get_db)):
    db_car_model = CarModel(name=car_model.name, car_brand_id=car_model.car_brand_id)
    db.add(db_car_model)
    db.commit()
    db.refresh(db_car_model)
    return db_car_model

@app.get("/car_models/{car_model_id}", response_model=CarModel)
def read_car_model(car_model_id: int, db: Session = Depends(get_db)):
    db_car_model = db.query(CarModel).filter(CarModel.id == car_model_id).first()
    if db_car_model is None:
        raise HTTPException(status_code=404, detail="Car model not found")
    return db_car_model

@app.put("/car_models/{car_model_id}", response_model=CarModel)
def update_car_model(car_model_id: int, car_model: CarModelUpdate, db: Session = Depends(get_db)):
    db_car_model = db.query(CarModel).filter(CarModel.id == car_model_id).first()
    if db_car_model is None:
        raise HTTPException(status_code=404, detail="Car model not found")
    for field, value in car_model:
        setattr(db_car_model, field, value)
    db.commit()
    db.refresh(db_car_model)
    return db_car_model

@app.delete("/car_models/{car_model_id}")
def delete_car_model(car_model_id: int, db: Session = Depends(get_db)):
    db_car_model = db.query(CarModel).filter(CarModel.id == car_model_id).first()
    if db_car_model is None:
        raise HTTPException(status_code=404, detail="Car model not found")
    db.delete(db_car_model)
    db.commit()
    return {"message": "Car model deleted"}

@app.get("/cars/{brand_name}")
def read_cars_by_brand(brand_name: str, db: Session = Depends(get_db)):
    db_car_brand = db.query(CarBrand).filter(CarBrand.name == brand_name).first()
    if db_car_brand is None:
        raise HTTPException(status_code=404, detail="Car brand not found")
    db_car_models = db.query(CarModel).filter(CarModel.car_brand_id == db_car_brand.id).all()
    return db_car_models

@app.get("/cars/search")
def search_cars(keywords: str, db: Session = Depends(get_db)):
    db_car_models = db.query(CarModel).filter(CarModel.name.ilike(f"%{keywords}%")).all()
    return db_car_models