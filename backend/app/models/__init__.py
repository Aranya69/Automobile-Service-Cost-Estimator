# Import every model here so Flask-Migrate can see it.
from .user import User  # noqa: F401
from .vehicle import Vehicle  # noqa: F401
from .price import JobPart, LabourRate, Part, PartPrice, ServiceJob  # noqa: F401
from .estimate import Estimate, EstimateItem  # noqa: F401
