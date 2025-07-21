import pytest
from users.models import CustomUser  # Make sure this points to your actual custom user model
from reviews.models import Review
from django.contrib.contenttypes.models import ContentType


@pytest.mark.django_db
def test_review_creation():
  
    reviewer = CustomUser.objects.create_user(
        username="rev", email="r@view.com", password="pass"
    )
    reviewee = CustomUser.objects.create_user(
        username="ee", email="ee@view.com", password="pass"
    )

   
    content_type = ContentType.objects.get_for_model(CustomUser)

    review = Review.objects.create(
        reviewer=reviewer,
        reviewee=reviewee,
        rating=5,
        content_type=content_type,
        object_id=reviewee.id
    )


    assert review.rating == 5
    assert review.reviewer == reviewer
    assert review.reviewee == reviewee
