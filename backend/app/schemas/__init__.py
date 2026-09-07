"""Pydantic request and response models.

Kept in a separate layer from the ORM so the wire format can evolve without a
migration, and so a field can never leak simply because it exists on a model --
see ``ExerciseRead``, which has no ``correct_answer`` field at all.
"""
