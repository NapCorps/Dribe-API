import uuid
import math
import warnings
import functools

from flask_bcrypt import generate_password_hash, check_password_hash

from app.google.matrix import MatrixApi
from app.models.settings import Settings


def deprecated(func):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in warning beign emitted when
    the function is used.
    Source url: https://wiki.python.org/moin/
    PythonDecoratorLibrary#Smart_deprecation_warnings_.
    28with_valid_filenames.2C_line_numbers.2C_etc..29
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)

    return new_func


class ModelHelper:
    @staticmethod
    def get_unique_id():
        return str(uuid.uuid4())

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def check_hash(password, hash):
        return check_password_hash(hash, password)


class MathHelper:
    __MILE_FACTOR__ = 0.000621371

    @staticmethod
    def get_distance(driver_pool, request):
        driver_coordinates = driver_pool.get_coordinates()
        request_coordinates = request.get_coordinates()
        return {
            "driver": driver_pool.driver,
            "distance": MathHelper._distance_formula(driver_coordinates, request_coordinates)
        }

    @staticmethod
    def _distance_formula(point_one, point_two):
        """
        This function implements d = sqrt( (x_2 - x_1)^2 + (y_2 - y_1)^2 )
        from two tuples that store the points
        """
        delta_x = point_two[0] - point_one[0]
        delta_y = point_two[1] - point_one[1]
        d = math.sqrt(math.pow(delta_x, 2) + math.pow(delta_y, 2))
        return d

    @staticmethod
    def calculate_estimate(request):
        response = MatrixApi(request=request).get_matrix_info()
        return MathHelper._ride_estimator(response[0], response[1])

    @staticmethod
    def _ride_estimator(distance, time):
        rates_info = Settings.get_rates()
        br = rates_info["base_rate"]
        dr = rates_info["distance_rate"]
        tr = rates_info["time_rate"]
        distance = MathHelper._meters_to_miles(distance)
        time /= 60
        total = br + (distance * dr) + (time * tr)
        if Settings.is_peak_chargeable():
            total += rates_info["peak_surcharge"]
        return round(total, 2)

    @staticmethod
    def _meters_to_miles(meters):
        return meters * MathHelper.__MILE_FACTOR__
