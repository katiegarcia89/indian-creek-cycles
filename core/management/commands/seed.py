"""
Management command to seed the database with sample data for Indian Creek Cycles.
This creates 30+ bikes, 10 trails, accessories, promo codes, and reviews.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files import File
from datetime import datetime, timedelta
import os

from accounts.models import User
from bikes.models import BikeCategory, BikeSize, Bike, Accessory, BikeAccessory
from reservations.models import PromoCode
from reviews.models import Review
from core.models import Trail


class Command(BaseCommand):
    help = 'Seed the database with sample data for demonstration'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seeding...')
        self.stdout.write('This will create 30+ bikes, 10 trails, and sample data.')
        
        # Create data in order
        self.create_users()
        self.create_bike_categories()
        self.create_bike_sizes()
        self.create_bikes()
        self.create_accessories()
        self.create_trails()
        self.create_promo_codes()
        self.create_reviews()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Created:'))
        self.stdout.write(self.style.SUCCESS(f'  - {User.objects.count()} users'))
        self.stdout.write(self.style.SUCCESS(f'  - {BikeCategory.objects.count()} categories'))
        self.stdout.write(self.style.SUCCESS(f'  - {Bike.objects.count()} bikes'))
        self.stdout.write(self.style.SUCCESS(f'  - {Accessory.objects.count()} accessories'))
        self.stdout.write(self.style.SUCCESS(f'  - {Trail.objects.count()} trails'))
        self.stdout.write(self.style.SUCCESS(f'  - {Review.objects.count()} reviews'))
    
    def create_users(self):
        """Create sample users."""
        self.stdout.write('\nCreating users...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@indiancreekcycles.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                phone='(555) 000-0000'
            )
            self.stdout.write(f'  ✅ Created admin user: {admin.username}')
        
        # Create regular users
        users_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'password': 'demo123', 'first_name': 'John', 'last_name': 'Doe', 'phone': '(555) 123-4567'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'password': 'demo123', 'first_name': 'Jane', 'last_name': 'Smith', 'phone': '(555) 234-5678'},
            {'username': 'mike_johnson', 'email': 'mike@example.com', 'password': 'demo123', 'first_name': 'Mike', 'last_name': 'Johnson', 'phone': '(555) 345-6789'},
            {'username': 'sarah_williams', 'email': 'sarah@example.com', 'password': 'demo123', 'first_name': 'Sarah', 'last_name': 'Williams', 'phone': '(555) 456-7890'},
            {'username': 'tom_brown', 'email': 'tom@example.com', 'password': 'demo123', 'first_name': 'Tom', 'last_name': 'Brown', 'phone': '(555) 567-8901'},
            {'username': 'lisa_davis', 'email': 'lisa@example.com', 'password': 'demo123', 'first_name': 'Lisa', 'last_name': 'Davis', 'phone': '(555) 678-9012'},
        ]
        
        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                password = user_data.pop('password')
                user = User.objects.create_user(**user_data)
                user.set_password(password)
                user.save()
                self.stdout.write(f'  ✅ Created user: {user.username}')
    
    def create_bike_categories(self):
        """Create bike categories."""
        self.stdout.write('\nCreating bike categories...')
        
        categories = [
            {'name': 'Adult Bikes', 'slug': 'adult-bikes', 'description': 'Premium bikes designed for adult riders of all skill levels. Perfect for casual rides, commuting, and fitness.', 'display_order': 1},
            {'name': 'Kids Bikes', 'slug': 'kids-bikes', 'description': 'Safe, durable, and fun bikes for young riders. Various sizes available for different age groups.', 'display_order': 2},
            {'name': 'Mountain Bikes', 'slug': 'mountain-bikes', 'description': 'Rugged bikes built for off-road adventures. Full suspension and hardtail options available.', 'display_order': 3},
            {'name': 'Tandem Bikes', 'slug': 'tandem-bikes', 'description': 'Two-seat bikes perfect for couples, friends, or parent-child riding. Double the fun!', 'display_order': 4},
            {'name': 'Hybrid Bikes', 'slug': 'hybrid-bikes', 'description': 'Versatile bikes that combine the best of road and mountain bikes. Great for mixed terrain.', 'display_order': 5},
        ]
        
        for cat_data in categories:
            category, created = BikeCategory.objects.get_or_create(slug=cat_data['slug'], defaults=cat_data)
            if created:
                self.stdout.write(f'  ✅ Created category: {category.name}')
    
    def create_bike_sizes(self):
        """Create bike sizes."""
        self.stdout.write('\nCreating bike sizes...')
        
        sizes = [
            {'size_inches': 12, 'description': 'Balance bike size for toddlers learning to ride. No pedals.', 'recommended_height': '2\'6" - 3\'0"', 'recommended_age': '2-3 years'},
            {'size_inches': 16, 'description': 'Perfect for young children ages 4-6. Lightweight frame with training wheels available.', 'recommended_height': '3\'6" - 4\'0"', 'recommended_age': '4-6 years'},
            {'size_inches': 20, 'description': 'Ideal for children ages 6-9. Great for building confidence and skills.', 'recommended_height': '4\'0" - 4\'4"', 'recommended_age': '6-9 years'},
            {'size_inches': 24, 'description': 'Suitable for older children and young teens. Transition to adult-sized bikes.', 'recommended_height': '4\'4" - 4\'8"', 'recommended_age': '9-12 years'},
            {'size_inches': 26, 'description': 'Standard adult bike size. Versatile and comfortable for most riders.', 'recommended_height': '5\'0" - 5\'8"', 'recommended_age': '13+ years'},
            {'size_inches': 27, 'description': 'Popular mountain bike size. Great for trail riding and rough terrain.', 'recommended_height': '5\'4" - 5\'10"', 'recommended_age': '13+ years'},
            {'size_inches': 28, 'description': 'Large adult bike size. Ideal for taller riders and long-distance comfort.', 'recommended_height': '5\'10" - 6\'4"', 'recommended_age': '13+ years'},
            {'size_inches': 29, 'description': 'Extra-large wheels for maximum speed and efficiency. Popular for mountain biking.', 'recommended_height': '5\'10" and taller', 'recommended_age': 'Adult'},
        ]
        
        for size_data in sizes:
            size, created = BikeSize.objects.get_or_create(size_inches=size_data['size_inches'], defaults=size_data)
            if created:
                self.stdout.write(f'  ✅ Created size: {size}')
    
    def create_bikes(self):
        """Create 30+ sample bikes with images."""
        self.stdout.write('\nCreating 30+ bikes...')
        
        # Get categories
        adult_cat = BikeCategory.objects.get(slug='adult-bikes')
        kids_cat = BikeCategory.objects.get(slug='kids-bikes')
        mountain_cat = BikeCategory.objects.get(slug='mountain-bikes')
        tandem_cat = BikeCategory.objects.get(slug='tandem-bikes')
        hybrid_cat = BikeCategory.objects.get(slug='hybrid-bikes')
        
        # Get sizes
        size_12 = BikeSize.objects.get(size_inches=12)
        size_16 = BikeSize.objects.get(size_inches=16)
        size_20 = BikeSize.objects.get(size_inches=20)
        size_24 = BikeSize.objects.get(size_inches=24)
        size_26 = BikeSize.objects.get(size_inches=26)
        size_27 = BikeSize.objects.get(size_inches=27)
        size_28 = BikeSize.objects.get(size_inches=28)
        size_29 = BikeSize.objects.get(size_inches=29)
        
        bikes = [
            # ========== ADULT BIKES (10 bikes) ==========
            {
                'name': 'City Cruiser Deluxe',
                'slug': 'city-cruiser-deluxe',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_26,
                'description': 'A comfortable, stylish cruiser perfect for city rides and beach paths. Features a step-through frame for easy mounting.',
                'features': 'Step-through aluminum frame\n7-speed Shimano gears\nComfortable padded saddle\nFront and rear fenders\nRear rack included',
                'price_per_day': 35.00,
                'price_per_hour': 10.00,
                'quantity_total': 5,
                'image_path': 'bikes/adult/city-cruiser-deluxe.jpg'
            },
            {
                'name': 'Road Runner Pro',
                'slug': 'road-runner-pro',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_28,
                'description': 'Lightweight road bike designed for speed and efficiency. Perfect for fitness rides and long-distance touring.',
                'features': 'Lightweight carbon frame\n21-speed Shimano gears\nDrop handlebars\nClipless pedal compatible\nAerodynamic design',
                'price_per_day': 45.00,
                'price_per_hour': 12.00,
                'quantity_total': 4,
                'image_path': 'bikes/adult/road-runner-pro.jpg'
            },
            {
                'name': 'Comfort Glide',
                'slug': 'comfort-glide',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_26,
                'description': 'An ultra-comfortable bike with an upright riding position. Great for casual rides and sightseeing.',
                'features': 'Upright riding position\nSuspension seat post\nWide comfort tires\nAdjustable handlebars\nEasy-to-use gears',
                'price_per_day': 30.00,
                'price_per_hour': 8.00,
                'quantity_total': 6,
                'image_path': 'bikes/adult/comfort-glide.jpg'
            },
            {
                'name': 'Beach Cruiser Classic',
                'slug': 'beach-cruiser-classic',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_26,
                'description': 'Classic beach cruiser with retro styling. Wide comfortable seat, coaster brakes, and a fun mint green color.',
                'features': 'Classic steel frame\nSingle speed with coaster brake\nWide padded saddle\nWhite wall tires\nFront basket included',
                'price_per_day': 28.00,
                'price_per_hour': 8.00,
                'quantity_total': 4,
                'image_path': 'bikes/adult/beach-cruiser-classic.jpg'
            },
            {
                'name': 'Urban Commuter Electric',
                'slug': 'urban-commuter-electric',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_28,
                'description': 'Electric-assist hybrid bike perfect for commuting. Integrated battery provides up to 40 miles of assisted riding.',
                'features': 'Electric assist motor\nIntegrated battery\nStep-through frame\nFront basket and fenders\nLED lights',
                'price_per_day': 55.00,
                'price_per_hour': 18.00,
                'quantity_total': 3,
                'image_path': 'bikes/adult/urban-commuter-electric.jpg'
            },
            {
                'name': 'Folding Commuter',
                'slug': 'folding-commuter',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_20,
                'description': 'Compact folding bike perfect for urban commuting and easy storage. Folds in seconds for transport on trains or in car trunks.',
                'features': 'Aluminum folding frame\n7-speed gears\n20-inch wheels\nRear rack\nFolds in 10 seconds',
                'price_per_day': 32.00,
                'price_per_hour': 10.00,
                'quantity_total': 4,
                'image_path': 'bikes/adult/folding-commuter.jpg'
            },
            {
                'name': 'Recumbent Cruiser',
                'slug': 'recumbent-cruiser',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_26,
                'description': 'Three-wheel recumbent bike with laid-back seating position. Perfect for seniors or riders with back issues.',
                'features': 'Three-wheel stability\nReclined seating position\nMesh comfort seat\nEasy step-through entry\nSmooth riding experience',
                'price_per_day': 40.00,
                'price_per_hour': 12.00,
                'quantity_total': 2,
                'image_path': 'bikes/adult/recumbent-cruiser.jpg'
            },
            {
                'name': "Women's Road Bike",
                'slug': 'womens-road-bike',
                'category': adult_cat,
                'bike_type': 'adult',
                'size': size_27,
                'description': 'Women-specific road bike with compact geometry and components designed for female riders.',
                'features': 'Women-specific geometry\nCarbon fork\n18-speed gears\nWomen-specific saddle\nCompact handlebars',
                'price_per_day': 42.00,
                'price_per_hour': 12.00,
                'quantity_total': 3,
                'image_path': 'bikes/adult/womens-road-bike.jpg'
            },
            {
                'name': 'Sport Hybrid',
                'slug': 'sport-hybrid',
                'category': hybrid_cat,
                'bike_type': 'adult',
                'size': size_28,
                'description': 'Versatile hybrid bike that handles both pavement and light trails with ease.',
                'features': 'Lightweight aluminum frame\n24-speed gears\nFront suspension fork\n700c wheels\nAll-terrain tires',
                'price_per_day': 38.00,
                'price_per_hour': 11.00,
                'quantity_total': 5,
                'image_path': 'bikes/sport-hybrid-clean.png'
            },
            {
                'name': 'Fitness Trainer',
                'slug': 'fitness-trainer',
                'category': hybrid_cat,
                'bike_type': 'adult',
                'size': size_28,
                'description': 'Performance hybrid designed for fitness enthusiasts. Fast on roads, capable on light trails.',
                'features': 'Lightweight frame\nFlat handlebars\n27-speed gears\n700c performance wheels\nHydraulic disc brakes',
                'price_per_day': 40.00,
                'price_per_hour': 11.00,
                'quantity_total': 4,
                'image_path': 'bikes/fitness-trainer-clean.png'
            },
            
            # ========== KIDS BIKES (8 bikes) ==========
            {
                'name': 'Little Explorer',
                'slug': 'little-explorer',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_16,
                'description': 'A fun and safe starter bike for young children. Training wheels included and easily removable.',
                'features': 'Training wheels included\nCoaster brakes\nChain guard for safety\nAdjustable seat height\nBright, fun colors',
                'price_per_day': 15.00,
                'price_per_hour': 5.00,
                'quantity_total': 4,
                'image_path': 'bikes/kids/little-explorer.jpg'
            },
            {
                'name': 'Youth Adventurer',
                'slug': 'youth-adventurer',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_20,
                'description': 'Perfect for kids ready to explore. Lightweight and easy to handle with reliable brakes.',
                'features': 'Lightweight aluminum frame\nHand brakes\n6-speed gears\nReflectors for visibility\nKickstand included',
                'price_per_day': 20.00,
                'price_per_hour': 6.00,
                'quantity_total': 5,
                'image_path': 'bikes/kids/youth-adventurer.jpg'
            },
            {
                'name': 'Teen Trail Blazer',
                'slug': 'teen-trail-blazer',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_24,
                'description': 'A versatile bike for growing riders. Suitable for both neighborhood rides and light trails.',
                'features': 'Durable steel frame\n21-speed gears\nFront suspension\nAll-terrain tires\nQuick-release seat',
                'price_per_day': 25.00,
                'price_per_hour': 7.00,
                'quantity_total': 4,
                'image_path': 'bikes/kids/teen-trail-blazer.jpg'
            },
            {
                'name': 'Balance Bike',
                'slug': 'balance-bike',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_12,
                'description': 'Wooden balance bike for toddlers to learn balance before pedaling. No pedals, just push and glide.',
                'features': 'Natural wood frame\nNo pedals - balance training\nAdjustable seat height\nSoft grip handles\nLightweight design',
                'price_per_day': 12.00,
                'price_per_hour': 4.00,
                'quantity_total': 3,
                'image_path': 'bikes/kids/balance-bike.jpg'
            },
            {
                'name': 'BMX Freestyle',
                'slug': 'bmx-freestyle',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_20,
                'description': 'BMX freestyle bike for tricks and jumps. Chrome frame with pegs for stunts.',
                'features': 'Chrome steel frame\n20-inch wheels\nFront and rear pegs\nGyro brake system\nDirt jump style',
                'price_per_day': 22.00,
                'price_per_hour': 7.00,
                'quantity_total': 3,
                'image_path': 'bikes/kids/bmx-freestyle.jpg'
            },
            {
                'name': 'Kids Mountain Bike',
                'slug': 'kids-mountain-bike',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_24,
                'description': 'Real mountain bike scaled for kids. Front suspension and knobby tires for off-road fun.',
                'features': 'Hardtail frame\nFront suspension fork\n18-speed gears\nDisc brakes\nKnobby tires',
                'price_per_day': 28.00,
                'price_per_hour': 8.00,
                'quantity_total': 4,
                'image_path': 'bikes/kids-mountain-bike-clean.png'
            },
            {
                'name': 'Princess Bike',
                'slug': 'princess-bike',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_16,
                'description': 'Colorful bike for young girls with streamers, basket, and fun decorations.',
                'features': 'Colorful frame with decals\nTraining wheels\nFront basket\nHandlebar streamers\nCoaster brake',
                'price_per_day': 16.00,
                'price_per_hour': 5.00,
                'quantity_total': 3,
                'image_path': 'bikes/princess-bike-clean.png'
            },
            {
                'name': 'Superhero Bike',
                'slug': 'superhero-bike',
                'category': kids_cat,
                'bike_type': 'kids',
                'size': size_16,
                'description': 'Action-themed bike for young boys with bold colors and cool graphics.',
                'features': 'Bold colored frame\nTraining wheels\nNumber plate\nCool graphics\nCoaster brake',
                'price_per_day': 16.00,
                'price_per_hour': 5.00,
                'quantity_total': 3,
                'image_path': 'bikes/superhero-bike-clean.png'
            },
            
            # ========== MOUNTAIN BIKES (7 bikes) ==========
            {
                'name': 'Trail Master X1',
                'slug': 'trail-master-x1',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_27,
                'description': 'A capable hardtail mountain bike for trail adventures. Great for intermediate riders.',
                'features': 'Hardtail aluminum frame\nFront suspension fork\n27-speed gears\nHydraulic disc brakes\nTubeless-ready wheels',
                'price_per_day': 50.00,
                'price_per_hour': 15.00,
                'quantity_total': 4,
                'image_path': 'bikes/mountain/trail-master-x1.jpg'
            },
            {
                'name': 'Summit Pro Full Suspension',
                'slug': 'summit-pro-full-suspension',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_29,
                'description': 'Full suspension mountain bike for serious trail riding. Handles rough terrain with ease.',
                'features': 'Full suspension frame\nFront and rear shocks\n12-speed gears\nHydraulic disc brakes\nDropper seat post',
                'price_per_day': 75.00,
                'price_per_hour': 20.00,
                'quantity_total': 3,
                'image_path': 'bikes/mountain/summit-pro-full-suspension.jpg'
            },
            {
                'name': 'All-Terrain Explorer',
                'slug': 'all-terrain-explorer',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_29,
                'description': 'Versatile mountain bike suitable for various terrains. Perfect for exploring local trails.',
                'features': 'Aluminum hardtail frame\nLockout suspension fork\n24-speed gears\nMechanical disc brakes\nWide handlebars',
                'price_per_day': 45.00,
                'price_per_hour': 12.00,
                'quantity_total': 5,
                'image_path': 'bikes/all-terrain-explorer-clean.png'
            },
            {
                'name': 'Fat Trekker',
                'slug': 'fat-trekker',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_26,
                'description': 'Fat tire bike for sand, snow, and rough terrain. Extra wide tires provide incredible traction.',
                'features': 'Aluminum frame\nRigid fork\n4-inch wide tires\nDisc brakes\nSingle speed or 7-speed',
                'price_per_day': 48.00,
                'price_per_hour': 14.00,
                'quantity_total': 3,
                'image_path': 'bikes/mountain/fat-trekker.jpg'
            },
            {
                'name': 'Downhill Dominator',
                'slug': 'downhill-dominator',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_27,
                'description': 'Aggressive downhill mountain bike for steep descents and technical terrain.',
                'features': 'Full suspension DH frame\n200mm travel fork\n7-speed gears\nHydraulic disc brakes\nDouble-walled rims',
                'price_per_day': 85.00,
                'price_per_hour': 25.00,
                'quantity_total': 2,
                'image_path': 'bikes/downhill-dominator-clean.png'
            },
            {
                'name': 'Cross Country Racer',
                'slug': 'cross-country-racer',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_29,
                'description': 'Lightweight cross-country mountain bike for racing and fast trail riding.',
                'features': 'Carbon fiber frame\n100mm travel fork\n12-speed gears\nTubeless tires\nLightweight components',
                'price_per_day': 65.00,
                'price_per_hour': 18.00,
                'quantity_total': 3,
                'image_path': 'bikes/cross-country-racer-clean.png'
            },
            {
                'name': 'Trail Beginner',
                'slug': 'trail-beginner',
                'category': mountain_cat,
                'bike_type': 'mountain',
                'size': size_26,
                'description': 'Entry-level mountain bike perfect for beginners trying trail riding for the first time.',
                'features': 'Aluminum frame\nFront suspension\n21-speed gears\nV-brakes or disc brakes\nComfortable saddle',
                'price_per_day': 38.00,
                'price_per_hour': 11.00,
                'quantity_total': 5,
                'image_path': 'bikes/trail-beginner-clean.png'
            },
            
            # ========== TANDEM BIKES (5 bikes) ==========
            {
                'name': 'Couples Cruiser Tandem',
                'slug': 'couples-cruiser-tandem',
                'category': tandem_cat,
                'bike_type': 'adult',
                'size': size_26,
                'description': 'Classic tandem bike for two adult riders. Perfect for couples wanting to ride together.',
                'features': 'Steel tandem frame\nTwo seats in line\nSynchronized pedaling\n7-speed gears\nComfortable seats',
                'price_per_day': 60.00,
                'price_per_hour': 18.00,
                'quantity_total': 3,
                'image_path': 'bikes/tandem/couples-cruiser-tandem.jpg'
            },
            {
                'name': 'Family Fun Tandem',
                'slug': 'family-fun-tandem',
                'category': tandem_cat,
                'bike_type': 'adult',
                'size': size_24,
                'description': 'Tandem bike designed for parent-child riding. Adult in front, child in back with safety harness.',
                'features': 'Adjustable child seat\nSafety harness included\nCoaster brake for child\nHand brakes for adult\nStable design',
                'price_per_day': 45.00,
                'price_per_hour': 14.00,
                'quantity_total': 2,
                'image_path': 'bikes/tandem/family-fun-tandem.jpg'
            },
            {
                'name': 'Performance Tandem',
                'slug': 'performance-tandem',
                'category': tandem_cat,
                'bike_type': 'adult',
                'size': size_28,
                'description': 'High-performance tandem for serious riders. Lightweight and fast for long-distance rides.',
                'features': 'Lightweight aluminum frame\nDrop handlebars\n27-speed gears\nClipless pedals\nAerodynamic design',
                'price_per_day': 70.00,
                'price_per_hour': 20.00,
                'quantity_total': 2,
                'image_path': 'bikes/performance-tandem-clean.png'
            },
            {
                'name': 'Kid-Size Tandem',
                'slug': 'kid-size-tandem',
                'category': tandem_cat,
                'bike_type': 'kids',
                'size': size_20,
                'description': 'Smaller tandem bike designed for two children to ride together. Great for siblings!',
                'features': 'Child-sized frame\nTwo kid seats\nCoaster brakes\nTraining wheels available\nFun colors',
                'price_per_day': 30.00,
                'price_per_hour': 9.00,
                'quantity_total': 2,
                'image_path': 'bikes/kid-size-tandem-clean.png'
            },
            {
                'name': 'Recumbent Tandem',
                'slug': 'recumbent-tandem',
                'category': tandem_cat,
                'bike_type': 'adult',
                'size': size_26,
                'description': 'Unique recumbent tandem with side-by-side seating. Both riders recline in comfort.',
                'features': 'Side-by-side seating\nReclined position\nIndependent pedaling\nThree-wheel stability\nMaximum comfort',
                'price_per_day': 80.00,
                'price_per_hour': 24.00,
                'quantity_total': 1,
                'image_path': 'bikes/recumbent-tandem-clean.png'
            },
        ]
        
        media_root = 'media/'
        
        for bike_data in bikes:
            image_path = bike_data.pop('image_path', None)
            bike, created = Bike.objects.get_or_create(slug=bike_data['slug'], defaults=bike_data)
            
            if created:
                # Try to attach image if path exists
                if image_path:
                    full_path = os.path.join(media_root, image_path)
                    if os.path.exists(full_path):
                        try:
                            with open(full_path, 'rb') as img_file:
                                bike.image.save(os.path.basename(image_path), File(img_file), save=True)
                            self.stdout.write(f'  ✅ Created bike: {bike.name} (with image)')
                        except Exception as e:
                            self.stdout.write(f'  ✅ Created bike: {bike.name} (image error: {e})')
                    else:
                        self.stdout.write(f'  ✅ Created bike: {bike.name} (image not found)')
                else:
                    self.stdout.write(f'  ✅ Created bike: {bike.name}')
    
    def create_accessories(self):
        """Create bike accessories."""
        self.stdout.write('\nCreating accessories...')
        
        accessories = [
            {'name': 'Helmet - Adult', 'description': 'Comfortable, adjustable helmet with ventilation. Meets all safety standards.', 'category': 'safety', 'price': 0.00, 'price_per_day': 5.00, 'quantity_in_stock': 25},
            {'name': 'Helmet - Youth', 'description': 'Youth-sized helmet with fun designs. Adjustable fit for growing riders.', 'category': 'safety', 'price': 0.00, 'price_per_day': 4.00, 'quantity_in_stock': 20},
            {'name': 'Helmet - Child', 'description': 'Small helmet for children with bright colors and fun patterns.', 'category': 'safety', 'price': 0.00, 'price_per_day': 3.00, 'quantity_in_stock': 15},
            {'name': 'Bike Lock', 'description': 'Heavy-duty U-lock with cable. Keep your rental secure when stopping.', 'category': 'safety', 'price': 0.00, 'price_per_day': 3.00, 'quantity_in_stock': 30},
            {'name': 'Bike Basket', 'description': 'Front-mounted wire basket. Perfect for carrying personal items.', 'category': 'storage', 'price': 0.00, 'price_per_day': 4.00, 'quantity_in_stock': 20},
            {'name': 'Rear Rack Bag', 'description': 'Water-resistant bag that attaches to rear rack. Great for longer rides.', 'category': 'storage', 'price': 0.00, 'price_per_day': 5.00, 'quantity_in_stock': 15},
            {'name': 'Handlebar Bag', 'description': 'Small bag that attaches to handlebars. Perfect for phone and keys.', 'category': 'storage', 'price': 0.00, 'price_per_day': 3.00, 'quantity_in_stock': 18},
            {'name': 'Water Bottle & Cage', 'description': 'Insulated water bottle with mounting cage. Stay hydrated on your ride.', 'category': 'comfort', 'price': 0.00, 'price_per_day': 2.00, 'quantity_in_stock': 35},
            {'name': 'Phone Mount', 'description': 'Secure handlebar mount for smartphones. Great for navigation.', 'category': 'electronics', 'price': 0.00, 'price_per_day': 3.00, 'quantity_in_stock': 20},
            {'name': 'Bike Lights Set', 'description': 'Front and rear LED lights for visibility. Essential for evening rides.', 'category': 'safety', 'price': 0.00, 'price_per_day': 4.00, 'quantity_in_stock': 25},
            {'name': 'Gel Seat Cover', 'description': 'Extra padding for maximum comfort on longer rides.', 'category': 'comfort', 'price': 0.00, 'price_per_day': 3.00, 'quantity_in_stock': 20},
            {'name': 'Repair Kit', 'description': 'Basic repair kit with tire levers, patch kit, and multi-tool.', 'category': 'other', 'price': 0.00, 'price_per_day': 5.00, 'quantity_in_stock': 15},
            {'name': 'Bike Pump', 'description': 'Portable hand pump for on-the-go tire inflation.', 'category': 'other', 'price': 0.00, 'price_per_day': 3.00, 'quantity_in_stock': 12},
            {'name': 'Child Trailer', 'description': 'Two-seat trailer that attaches to adult bike. Perfect for young children.', 'category': 'other', 'price': 0.00, 'price_per_day': 15.00, 'quantity_in_stock': 4},
            {'name': 'Baby Seat', 'description': 'Front or rear-mounted child seat for toddlers. Safety harness included.', 'category': 'other', 'price': 0.00, 'price_per_day': 8.00, 'quantity_in_stock': 6},
        ]
        
        for acc_data in accessories:
            accessory, created = Accessory.objects.get_or_create(name=acc_data['name'], defaults=acc_data)
            if created:
                self.stdout.write(f'  ✅ Created accessory: {accessory.name}')
        
        # Link accessories to bikes
        self.stdout.write('Linking accessories to bikes...')
        helmet_adult = Accessory.objects.get(name='Helmet - Adult')
        helmet_youth = Accessory.objects.get(name='Helmet - Youth')
        helmet_child = Accessory.objects.get(name='Helmet - Child')
        bike_lock = Accessory.objects.get(name='Bike Lock')
        
        for bike in Bike.objects.filter(bike_type='adult'):
            BikeAccessory.objects.get_or_create(bike=bike, accessory=helmet_adult)
            BikeAccessory.objects.get_or_create(bike=bike, accessory=bike_lock)
        
        for bike in Bike.objects.filter(bike_type='kids', size__size_inches__gte=20):
            BikeAccessory.objects.get_or_create(bike=bike, accessory=helmet_youth)
        
        for bike in Bike.objects.filter(bike_type='kids', size__size_inches__lt=20):
            BikeAccessory.objects.get_or_create(bike=bike, accessory=helmet_child)
    
    def create_trails(self):
        """Create sample trails with images."""
        self.stdout.write('\nCreating trails...')
        
        trails = [
            {
                'name': 'Indian Creek Greenway',
                'description': 'A scenic paved trail following Indian Creek. Perfect for families and casual riders. Beautiful views of the creek and wildlife.',
                'difficulty': 'easy',
                'length_miles': 4.5,
                'estimated_time': '1-2 hours',
                'terrain': 'Paved path, mostly flat',
                'highlights': 'Creek views, wildlife spotting, picnic areas, rest stops',
                'is_featured': True,
                'image_path': 'trails/indian-creek-greenway.jpg'
            },
            {
                'name': 'Oak Ridge Loop',
                'description': 'A moderate loop through oak forests with some gentle hills. Great for intermediate riders looking for a bit of challenge.',
                'difficulty': 'moderate',
                'length_miles': 8.2,
                'estimated_time': '2-3 hours',
                'terrain': 'Mixed gravel and dirt, rolling hills',
                'highlights': 'Forest canopy, wildflowers in spring, bird watching',
                'is_featured': True,
                'image_path': 'trails/oak-ridge-loop-summer.jpg'
            },
            {
                'name': 'Summit Challenge Trail',
                'description': 'A challenging mountain bike trail with steep climbs and technical descents. For experienced riders only.',
                'difficulty': 'expert',
                'length_miles': 12.5,
                'estimated_time': '3-5 hours',
                'terrain': 'Technical singletrack, rocky sections, steep grades',
                'highlights': 'Panoramic summit views, rock gardens, stream crossings',
                'is_featured': True,
                'image_path': 'trails/summit-challenge-trail.jpg'
            },
            {
                'name': 'Riverside Park Path',
                'description': 'An easy, family-friendly path along the river. Great for kids and beginners.',
                'difficulty': 'easy',
                'length_miles': 3.0,
                'estimated_time': '45 min - 1 hour',
                'terrain': 'Paved, completely flat',
                'highlights': 'River views, playgrounds, fishing spots',
                'is_featured': False,
                'image_path': 'trails/riverside-park-path.jpg'
            },
            {
                'name': 'Maple Grove Trail',
                'description': 'A shaded woodland path with a smooth packed surface and colorful seasonal tree cover.',
                'difficulty': 'moderate',
                'length_miles': 4.7,
                'estimated_time': '1-2 hours',
                'terrain': 'Packed gravel and dirt, gentle curves',
                'highlights': 'Maple canopy, fall color, shaded turns, quiet woodland views',
                'is_featured': False,
                'image_path': 'trails/oak-ridge-loop.jpg'
            },
            {
                'name': 'Lakeside Loop',
                'description': 'Scenic loop around beautiful Lake Henderson. Flat and easy with stunning water views.',
                'difficulty': 'easy',
                'length_miles': 5.5,
                'estimated_time': '1.5-2 hours',
                'terrain': 'Paved path, flat',
                'highlights': 'Lake views, picnic areas, wildlife, fishing piers',
                'is_featured': True,
                'image_path': 'trails/lakeside-loop.jpg'
            },
            {
                'name': 'Heritage Park Loops',
                'description': 'Open natural-surface loops through meadow edges, grasses, and shaded tree lines.',
                'difficulty': 'easy',
                'length_miles': 5.2,
                'estimated_time': '1.5-2 hours',
                'terrain': 'Packed dirt and gravel, mostly flat',
                'highlights': 'Meadow edges, shade trees, open views, easy loop options',
                'is_featured': False,
                'image_path': 'trails/Heritage_Park_Loops.jpg'
            },
            {
                'name': 'Ridge Runner Trail',
                'description': 'Technical ridge-top trail with challenging climbs and fast descents.',
                'difficulty': 'difficult',
                'length_miles': 9.3,
                'estimated_time': '2.5-4 hours',
                'terrain': 'Rocky singletrack, steep sections',
                'highlights': 'Ridge views, technical sections, fast descents',
                'is_featured': True,
                'image_path': None
            },
            {
                'name': 'Cedar Valley Path',
                'description': 'Gentle valley trail following Cedar Creek. Shaded and cool, perfect for summer rides.',
                'difficulty': 'easy',
                'length_miles': 6.0,
                'estimated_time': '1.5-2 hours',
                'terrain': 'Paved and packed dirt, flat',
                'highlights': 'Creek access, shade trees, cool temperatures',
                'is_featured': False,
                'image_path': None
            },
            {
                'name': 'Black Diamond Run',
                'description': 'Expert-only downhill trail with jumps, drops, and technical features.',
                'difficulty': 'expert',
                'length_miles': 3.5,
                'estimated_time': '1-2 hours',
                'terrain': 'Technical downhill, jumps, berms',
                'highlights': 'Jumps, drops, berms, technical features',
                'is_featured': False,
                'image_path': None
            },
        ]
        
        media_root = 'media/'
        
        for trail_data in trails:
            image_path = trail_data.pop('image_path', None)
            trail, created = Trail.objects.get_or_create(name=trail_data['name'], defaults=trail_data)
            
            if created:
                if image_path:
                    full_path = os.path.join(media_root, image_path)
                    if os.path.exists(full_path):
                        try:
                            with open(full_path, 'rb') as img_file:
                                trail.image.save(os.path.basename(image_path), File(img_file), save=True)
                            self.stdout.write(f'  ✅ Created trail: {trail.name} (with image)')
                        except Exception as e:
                            self.stdout.write(f'  ✅ Created trail: {trail.name} (image error: {e})')
                    else:
                        self.stdout.write(f'  ✅ Created trail: {trail.name}')
                else:
                    self.stdout.write(f'  ✅ Created trail: {trail.name}')
    
    def create_promo_codes(self):
        """Create sample promo codes."""
        self.stdout.write('\nCreating promo codes...')
        
        promo_codes = [
            {'code': 'WELCOME20', 'description': '20% off your first rental', 'discount_type': 'percentage', 'discount_value': 20.00, 'valid_from': timezone.now(), 'valid_until': timezone.now() + timedelta(days=365), 'max_uses': 100, 'minimum_order': 25.00},
            {'code': 'FAMILY10', 'description': '$10 off family rentals (3+ bikes)', 'discount_type': 'fixed', 'discount_value': 10.00, 'valid_from': timezone.now(), 'valid_until': timezone.now() + timedelta(days=180), 'max_uses': 50, 'minimum_order': 75.00},
            {'code': 'WEEKEND15', 'description': '15% off weekend rentals', 'discount_type': 'percentage', 'discount_value': 15.00, 'valid_from': timezone.now(), 'valid_until': timezone.now() + timedelta(days=90), 'max_uses': 200, 'minimum_order': 30.00},
            {'code': 'TANDEM25', 'description': '25% off tandem bike rentals', 'discount_type': 'percentage', 'discount_value': 25.00, 'valid_from': timezone.now(), 'valid_until': timezone.now() + timedelta(days=120), 'max_uses': 50, 'minimum_order': 50.00},
            {'code': 'KIDSFREE', 'description': 'Free helmet with kids bike rental', 'discount_type': 'fixed', 'discount_value': 4.00, 'valid_from': timezone.now(), 'valid_until': timezone.now() + timedelta(days=60), 'max_uses': 100, 'minimum_order': 15.00},
        ]
        
        for promo_data in promo_codes:
            promo, created = PromoCode.objects.get_or_create(code=promo_data['code'], defaults=promo_data)
            if created:
                self.stdout.write(f'  ✅ Created promo code: {promo.code}')
    
    def create_reviews(self):
        """Create sample reviews."""
        self.stdout.write('\nCreating reviews...')
        
        users = list(User.objects.filter(is_staff=False))
        bikes = list(Bike.objects.all())
        
        reviews_data = [
            {'user': users[0] if len(users) > 0 else None, 'bike': bikes[0] if len(bikes) > 0 else None, 'rating': 5, 'title': 'Amazing family experience!', 'content': 'We rented bikes for a family outing and had an incredible time. The bikes were in perfect condition and the staff was super helpful. The Indian Creek trail was beautiful! Highly recommend for families.', 'is_approved': True, 'is_featured': True},
            {'user': users[1] if len(users) > 1 else None, 'bike': bikes[7] if len(bikes) > 7 else None, 'rating': 5, 'title': 'Great mountain bikes!', 'content': 'Rented the Trail Master for a day of riding. The bike performed flawlessly on the Summit Challenge trail. Will definitely rent again!', 'is_approved': True, 'is_featured': True},
            {'user': users[2] if len(users) > 2 else None, 'bike': bikes[10] if len(bikes) > 10 else None, 'rating': 5, 'title': 'Perfect for kids', 'content': 'My kids loved the Little Explorer bikes. They were the perfect size and the training wheels gave them confidence. Great family activity!', 'is_approved': True, 'is_featured': True},
            {'user': users[3] if len(users) > 3 else None, 'bike': bikes[2] if len(bikes) > 2 else None, 'rating': 5, 'title': 'Excellent service and quality', 'content': 'From booking online to returning the bikes, everything was smooth and easy. The waiver process was quick and the bikes were top quality. Will be back!', 'is_approved': True, 'is_featured': False},
            {'user': users[4] if len(users) > 4 else None, 'bike': bikes[15] if len(bikes) > 15 else None, 'rating': 4, 'title': 'Good value for money', 'content': 'Reasonable prices for quality bikes. The accessories like helmets and locks were included which was nice. Recommended!', 'is_approved': True, 'is_featured': False},
            {'user': users[5] if len(users) > 5 else None, 'bike': bikes[20] if len(bikes) > 20 else None, 'rating': 5, 'title': 'Best bike rental in the area', 'content': 'I have tried several bike rental places and Indian Creek Cycles is by far the best. Great selection, fair prices, and knowledgeable staff.', 'is_approved': True, 'is_featured': True},
            {'user': users[0] if len(users) > 0 else None, 'bike': bikes[25] if len(bikes) > 25 else None, 'rating': 5, 'title': 'Tandem bike was so much fun!', 'content': 'My wife and I rented the couples tandem for our anniversary. It was such a unique experience riding together! The bike was well-maintained and comfortable.', 'is_approved': True, 'is_featured': True},
            {'user': users[1] if len(users) > 1 else None, 'bike': bikes[12] if len(bikes) > 12 else None, 'rating': 4, 'title': 'Great BMX for my son', 'content': 'Rented the BMX freestyle for my son\'s birthday. He had a blast at the skate park. Bike was in great condition.', 'is_approved': True, 'is_featured': False},
            {'user': users[2] if len(users) > 2 else None, 'bike': bikes[5] if len(bikes) > 5 else None, 'rating': 5, 'title': 'Electric bike was a game changer', 'content': 'The electric commuter bike made getting around so easy. Battery lasted all day and the pedal assist was perfect for hills.', 'is_approved': True, 'is_featured': False},
            {'user': users[3] if len(users) > 3 else None, 'bike': bikes[18] if len(bikes) > 18 else None, 'rating': 5, 'title': 'Fat bike on the beach was awesome', 'content': 'Took the Fat Trekker to the beach and it handled the sand perfectly. Such a fun and unique experience!', 'is_approved': True, 'is_featured': True},
        ]
        
        for review_data in reviews_data:
            if review_data['user'] and review_data['bike']:
                review, created = Review.objects.get_or_create(
                    user=review_data['user'],
                    bike=review_data['bike'],
                    defaults={
                        'rating': review_data['rating'],
                        'title': review_data['title'],
                        'content': review_data['content'],
                        'is_approved': review_data['is_approved'],
                        'is_featured': review_data['is_featured']
                    }
                )
                if created:
                    self.stdout.write(f'  ✅ Created review: {review.title}')
