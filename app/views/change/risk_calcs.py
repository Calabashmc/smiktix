from sqlalchemy import select
from ...model import db
from ...model.model_cmdb import CmdbConfigurationItem
from ...model.lookup_tables import Importance

def ci_importance_risk(ci_id, change_timing):
    # Define the scoring tables as dictionaries. The variables are:
    # (importance, operational_hours, change_timing): {base_score, change_timing_modifier}
    ci_scoring_table = {
        ("Platinum", "BH", "in_hours"): {"base_score": 5, "timing_modifier": 5},
        ("Platinum", "BH", "after_hours"): {"base_score": 5, "timing_modifier": 2},
        ("Platinum", "BH", "change_window"): {"base_score": 5, "timing_modifier": 1},
        ("Platinum", "24x7", "in_hours"): {"base_score": 7, "timing_modifier": 3},
        ("Platinum", "24x7", "after_hours"): {"base_score": 7, "timing_modifier": 2},
        ("Platinum", "24x7", "change_window"): {"base_score": 7, "timing_modifier": 1},
        ("Gold", "BH", "in_hours"): {"base_score": 4, "timing_modifier": 3},
        ("Gold", "BH", "after_hours"): {"base_score": 4, "timing_modifier": 2},
        ("Gold", "BH", "change_window"): {"base_score": 4, "timing_modifier": 1},
        ("Gold", "24x7", "in_hours"): {"base_score": 6, "timing_modifier": 3},
        ("Gold", "24x7", "after_hours"): {"base_score": 6, "timing_modifier": 2},
        ("Gold", "24x7", "change_window"): {"base_score": 6, "timing_modifier": 1},
        ("Silver", "BH", "in_hours"): {"base_score": 3, "timing_modifier": 3},
        ("Silver", "BH", "after_hours"): {"base_score": 3, "timing_modifier": 2},
        ("Silver", "BH", "change_window"): {"base_score": 3, "timing_modifier": 1},
        ("Silver", "24x7", "in_hours"): {"base_score": 5, "timing_modifier": 3},
        ("Silver", "24x7", "after_hours"): {"base_score": 5, "timing_modifier": 2},
        ("Silver", "24x7", "change_window"): {"base_score": 5, "timing_modifier": 1},
        ("Bronze", "BH", "in_hours"): {"base_score": 2, "timing_modifier": 3},
        ("Bronze", "BH", "after_hours"): {"base_score": 2, "timing_modifier": 2},
        ("Bronze", "BH", "change_window"): {"base_score": 2, "timing_modifier": 1},
        ("Bronze", "24x7", "in_hours"): {"base_score": 4, "timing_modifier": 3},
        ("Bronze", "24x7", "after_hours"): {"base_score": 4, "timing_modifier": 2},
        ("Bronze", "24x7", "change_window"): {"base_score": 4, "timing_modifier": 1},
    }


    if ci_id:
        metallic = db.session.execute(
            select(Importance)
            .join(CmdbConfigurationItem, CmdbConfigurationItem.importance_id == Importance.id)
            .where(CmdbConfigurationItem.id == ci_id)
        ).scalar_one_or_none()

        if metallic is None:
            return 0  # for some reason the record was not found

        ci_op_hours = db.session.execute(
            select(CmdbConfigurationItem.twentyfour_operation)
            .where(CmdbConfigurationItem.id == ci_id)
        ).scalar_one_or_none()

        if ci_op_hours:
            op_hours = "24x7"
        else:
            op_hours = "BH"
    else:
        return 0
    # todo check each combination and see if the expected CR is produced
    metalic_scores = ci_scoring_table.get((metallic.importance, op_hours, change_timing))
    metalic_points = metalic_scores.get("base_score") * metalic_scores.get("timing_modifier")
    return metalic_points


def risk_calcs(risk_checks, people_impact=0, change_timing="in_hours"):
    """
    Calculate the risk points based on impact and likelihood for each risk (security,
    data loss, customer, continuity, financial)
    return: risk points
    """
    risk_keys = risk_checks.keys()
    risk_points = {
        "high": 15,
        "medium": 10,
        "low": 1
    }

    risks_points = 0
    for key in risk_keys:
        impact = risk_checks[key][f'{key}-impact']
        probability = risk_checks[key][f'{key}-likelihood']
        risks_points += risk_points[impact.lower()] + risk_points[
            probability.lower()] * 0.5  # likelihood points is 50% of impact points

    if change_timing == "in_hours":
        risks_points += 5

    if change_timing == "after_hours":
        risks_points += 3

    risks_points += people_impact

    return risks_points