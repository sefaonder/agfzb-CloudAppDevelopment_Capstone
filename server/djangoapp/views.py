from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
# from .restapis import related methods
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, get_dealer_by_id_from_cf

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
base_url_dealership = "https://sefaonder111-3000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/"
base_url_api = "https://sefaonder111-5000.theiadockernext-0-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/"

# Create an `about` view to render a static about page
# def about(request):
# ...
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
#def contact(request):
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact_us.html', context)

# Create a `login_request` view to handle sign in request
# def login_request(request):
# ...
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('djangoapp:index')
        else:
            # If not, return to login page again
            return render(request, 'djangoapp:index', context)
    else:
        return render(request, 'djangoapp:index', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
# def registration_request(request):
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        print(request.POST)
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = base_url_dealership + "dealerships/get"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        context["dealership_list"] = dealerships
        print(context)
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}
        url = base_url_api + "api/get_reviews"
        url_dealer = base_url_dealership + "dealerships/get"
        # Get dealers from the URL
        review_details = get_dealer_reviews_from_cf(url,dealer_id)
        dealer = get_dealer_by_id_from_cf(url_dealer,dealer_id)
        # Concat all dealer's short name
        # Return a list of dealer short name
        print(dealer)
        context["dealer"] = dealer
        context["reviews"] = review_details
        print(context)
        return render(request, 'djangoapp/dealer_details.html', context)


# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    url_dealer = base_url_dealership + "dealerships/get"
    dealer = get_dealer_by_id_from_cf(url_dealer, dealer_id)
    context["dealer"] = dealer
    if request.method == 'GET':
        cars = CarModel.objects.all()
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
            first_name = user.first_name
            last_name = user.last_name
            full_name = f"{first_name} {last_name}"
            print(request.POST)
            payload = dict()
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)

            payload["time"] = datetime.utcnow().isoformat()
            payload["name"] = full_name
            payload["dealership"] = dealer_id
            payload["id"] = dealer_id
            payload["review"] = request.POST["content"]
            
            # Check if "purchasecheck" is checked
            if "purchasecheck" in request.POST and request.POST["purchasecheck"] == 'on':
                payload["purchase"] = True
                payload["purchase_date"] = request.POST["purchasedate"]
                payload["car_make"] = car.make.name
                payload["car_model"] = car.name
                payload["car_year"] = int(car.year)
            else:
                payload["purchase"] = False
            
            json_payload = {}
            json_payload["review"] = payload
            review_url = base_url_api + "/post_review"
            post_request(review_url, json_payload, id=dealer_id)
        return redirect("djangoapp:dealer_details", id=dealer_id)


