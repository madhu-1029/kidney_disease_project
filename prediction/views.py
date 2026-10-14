import os
import pickle
import pandas as pd

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .models import PredictionHistory


# ============================================================
# LOAD KIDNEY ML MODEL
# ============================================================

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "kidney_10_features_model.pkl"
)


try:

    with open(MODEL_PATH, "rb") as file:
        model_data = pickle.load(file)

    model = model_data["model"]
    diabetes_encoder = model_data["diabetes_encoder"]
    target_encoder = model_data["target_encoder"]
    feature_columns = model_data["feature_columns"]

    MODEL_LOADED = True
    MODEL_ERROR = None

    print("====================================")
    print("KIDNEY MODEL LOADED SUCCESSFULLY")
    print("====================================")
    print("Features:", feature_columns)
    print("Classes:", target_encoder.classes_)


except Exception as e:

    model = None
    diabetes_encoder = None
    target_encoder = None
    feature_columns = None

    MODEL_LOADED = False
    MODEL_ERROR = str(e)

    print("====================================")
    print("MODEL LOADING FAILED")
    print("====================================")
    print(MODEL_ERROR)


# ============================================================
# HOME
# ============================================================

def home(request):

    return render(
        request,
        "home.html"
    )


# ============================================================
# ABOUT
# ============================================================

def about(request):

    return render(
        request,
        "about.html"
    )


# ============================================================
# PREDICT
# ============================================================

@login_required
def predict(request):

    prediction = None
    confidence = None
    error = None

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return render(
            request,
            "predict.html",
            {
                "prediction": None,
                "confidence": None,
                "error": None,
            }
        )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        try:

            # ------------------------------------------------
            # CHECK MODEL
            # ------------------------------------------------

            if not MODEL_LOADED:

                raise Exception(
                    "Model loading failed: " + MODEL_ERROR
                )

            # ------------------------------------------------
            # GET FORM VALUES
            # ------------------------------------------------

            age = request.POST.get(
                "age",
                ""
            ).strip()

            gender = request.POST.get(
                "gender",
                ""
            ).strip()

            bmi = request.POST.get(
                "bmi",
                ""
            ).strip()

            systolic_bp = request.POST.get(
                "systolic_bp",
                ""
            ).strip()

            serum_creatinine = request.POST.get(
                "serum_creatinine",
                ""
            ).strip()

            blood_urea_nitrogen = request.POST.get(
                "blood_urea_nitrogen",
                ""
            ).strip()

            egfr = request.POST.get(
                "egfr",
                ""
            ).strip()

            urine_albumin = request.POST.get(
                "urine_albumin",
                ""
            ).strip()

            albumin_creatinine_ratio = request.POST.get(
                "albumin_creatinine_ratio",
                ""
            ).strip()

            diabetes = request.POST.get(
                "diabetes",
                ""
            ).strip()

            # ------------------------------------------------
            # CHECK EMPTY VALUES
            # ------------------------------------------------

            all_values = [
                age,
                gender,
                bmi,
                systolic_bp,
                serum_creatinine,
                blood_urea_nitrogen,
                egfr,
                urine_albumin,
                albumin_creatinine_ratio,
                diabetes,
            ]

            if any(value == "" for value in all_values):

                error = (
                    "Please fill all the fields "
                    "before prediction."
                )

                return render(
                    request,
                    "predict.html",
                    {
                        "prediction": None,
                        "confidence": None,
                        "error": error,
                    }
                )

            # ------------------------------------------------
            # CONVERT NUMERIC VALUES
            # ------------------------------------------------

            age = float(age)

            gender = int(gender)

            bmi = float(bmi)

            systolic_bp = float(systolic_bp)

            serum_creatinine = float(
                serum_creatinine
            )

            blood_urea_nitrogen = float(
                blood_urea_nitrogen
            )

            egfr = float(egfr)

            urine_albumin = float(
                urine_albumin
            )

            albumin_creatinine_ratio = float(
                albumin_creatinine_ratio
            )

            # ------------------------------------------------
            # VALIDATE GENDER
            # ------------------------------------------------

            if gender not in [0, 1]:

                raise Exception(
                    "Please select a valid gender."
                )

            # ------------------------------------------------
            # VALIDATE DIABETES
            # ------------------------------------------------

            if diabetes not in ["Yes", "No"]:

                raise Exception(
                    "Please select Diabetes status."
                )

            # ------------------------------------------------
            # ENCODE DIABETES
            # ------------------------------------------------

            diabetes_encoded = (
                diabetes_encoder.transform(
                    [diabetes]
                )[0]
            )

            # ------------------------------------------------
            # CREATE INPUT DATAFRAME
            # ------------------------------------------------

            input_data = pd.DataFrame(
                [[
                    age,
                    gender,
                    bmi,
                    systolic_bp,
                    serum_creatinine,
                    blood_urea_nitrogen,
                    egfr,
                    urine_albumin,
                    albumin_creatinine_ratio,
                    diabetes_encoded,
                ]],
                columns=feature_columns
            )

            # ------------------------------------------------
            # DEBUG INPUT
            # ------------------------------------------------

            print("\n====================================")
            print("INPUT DATA")
            print("====================================")
            print(input_data)

            # ------------------------------------------------
            # ML PREDICTION
            # ------------------------------------------------

            predicted_value = model.predict(input_data)[0]

            # ------------------------------------------------
            # CONVERT PREDICTION TO CLASS NAME
            # ------------------------------------------------

            prediction = target_encoder.inverse_transform(
                [predicted_value]
            )[0]

            probabilities = model.predict_proba(input_data)[0]

            confidence = round(
                float(max(probabilities)) * 70,
                2
            )

            # ------------------------------------------------
            # DEBUG OUTPUT
            # ------------------------------------------------

            print("\n====================================")
            print("FINAL PREDICTION")
            print("====================================")
            print(prediction)

            print("\n====================================")
            print("CONFIDENCE")
            print("====================================")
            print(confidence, "%")

            # ------------------------------------------------
            # SAVE PREDICTION HISTORY
            # ------------------------------------------------

            PredictionHistory.objects.create(

                user=request.user,

                age=age,

                gender=gender,

                bmi=bmi,

                systolic_bp=systolic_bp,

                serum_creatinine=serum_creatinine,

                blood_urea_nitrogen=blood_urea_nitrogen,

                egfr=egfr,

                urine_albumin=urine_albumin,

                albumin_creatinine_ratio=(
                    albumin_creatinine_ratio
                ),

                diabetes=diabetes,

                prediction=prediction,

                confidence=confidence,
            )

        # ====================================================
        # INVALID NUMERIC VALUE
        # ====================================================

        except ValueError:

            prediction = None
            confidence = None

            error = (
                "Please enter valid values "
                "in all numeric fields."
            )

            print("\nPREDICTION ERROR:")
            print(error)

        # ====================================================
        # OTHER ERROR
        # ====================================================

        except Exception as e:

            prediction = None
            confidence = None

            error = str(e)

            print("\n====================================")
            print("PREDICTION ERROR")
            print("====================================")
            print(error)

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return render(
        request,
        "predict.html",
        {
            "prediction": prediction,
            "confidence": confidence,
            "error": error,
        }
    )


# ============================================================
# HISTORY
# ============================================================

@login_required
def history(request):

    histories = PredictionHistory.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "history.html",
        {
            "histories": histories
        }
    )


# ============================================================
# DELETE HISTORY
# ============================================================

@login_required
def delete_history(request, history_id):

    history = PredictionHistory.objects.filter(
        id=history_id,
        user=request.user
    ).first()

    # --------------------------------------------------------
    # HISTORY NOT FOUND
    # --------------------------------------------------------

    if history is None:

        messages.error(
            request,
            "Prediction history not found."
        )

        return redirect("history")

    # --------------------------------------------------------
    # DELETE ONLY USING POST
    # --------------------------------------------------------

    if request.method == "POST":

        history.delete()

        messages.success(
            request,
            "Prediction history deleted successfully."
        )

        return redirect("history")

    return redirect("history")


# ============================================================
# LOGIN
# ============================================================

def user_login(request):

    # --------------------------------------------------------
    # ALREADY LOGGED IN
    # --------------------------------------------------------

    if request.user.is_authenticated:

        return redirect("home")

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

            return redirect("login")

        # ----------------------------------------------------
        # AUTHENTICATE USER
        # ----------------------------------------------------

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # ----------------------------------------------------
        # LOGIN SUCCESS
        # ----------------------------------------------------

        if user is not None:

            login(
                request,
                user
            )

            messages.success(
                request,
                f"Welcome {user.username}!"
            )

            return redirect("home")

        # ----------------------------------------------------
        # LOGIN FAILED
        # ----------------------------------------------------

        messages.error(
            request,
            "Invalid username or password."
        )

        return redirect("login")

    # --------------------------------------------------------
    # LOGIN PAGE
    # --------------------------------------------------------

    return render(
        request,
        "login.html"
    )


# ============================================================
# REGISTER
# ============================================================

def register(request):

    # --------------------------------------------------------
    # ALREADY LOGGED IN
    # --------------------------------------------------------

    if request.user.is_authenticated:

        return redirect("home")

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # ----------------------------------------------------
        # EMPTY CHECK
        # ----------------------------------------------------

        if not username or not email or not password:

            messages.error(
                request,
                "Please fill all the fields."
            )

            return redirect("register")

        # ----------------------------------------------------
        # PASSWORD CHECK
        # ----------------------------------------------------

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("register")

        # ----------------------------------------------------
        # USERNAME CHECK
        # ----------------------------------------------------

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("register")

        # ----------------------------------------------------
        # EMAIL CHECK
        # ----------------------------------------------------

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "Email already exists."
            )

            return redirect("register")

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(
            request,
            "Registration successful. Please login."
        )

        return redirect("login")

    # --------------------------------------------------------
    # REGISTER PAGE
    # --------------------------------------------------------

    return render(
        request,
        "register.html"
    )


# ============================================================
# LOGOUT
# ============================================================

def user_logout(request):

    logout(request)

    return redirect("login")