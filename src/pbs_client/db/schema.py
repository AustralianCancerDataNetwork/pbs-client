"""PBS resource registry.

The resource models own their columns and primary keys.  This module only
connects those models to the public API endpoints and defines sync order.
"""

from dataclasses import dataclass

from pbs_client.db.model import (
    ATC,
    ApiChangelog,
    Base,
    Container,
    ContainerWholesalerRltd,
    Copayment,
    Criteria,
    CriteriaParameterRltd,
    DispensingRule,
    ExPrepSfpRltd,
    ExtemporaneousDrugTariff,
    ExtemporaneousIngredient,
    ExtemporaneousPreparation,
    Fee,
    Indication,
    Item,
    ItemAmt,
    ItemAtcRltd,
    ItemDispensingRuleRltd,
    ItemOrganisationRltd,
    ItemOverview,
    ItemPrescribingTxtRltd,
    ItemPricingEvent,
    ItemRestrictionRltd,
    MarkupBand,
    Organisation,
    Parameter,
    Prescriber,
    PrescribingTxt,
    Program,
    ProgramDispensingRules,
    RestrictionText,
    RstrctnPrscrbngTxtRltd,
    Schedule,
    StandardFormulaPreparations,
    SummaryOfChanges,
)


@dataclass(frozen=True, slots=True)
class ResourceSpec:
    """API metadata for one persisted PBS resource."""

    name: str
    endpoint: str
    model: type[Base]

    @property
    def model_name(self) -> str:
        return self.model.__name__

    @property
    def table_name(self) -> str:
        return self.model.__tablename__

    @property
    def fields(self) -> tuple[str, ...]:
        return tuple(
            column.name for column in self.model.__table__.columns if column.name != "raw_payload"
        )

    @property
    def primary_key(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.model.__table__.primary_key)


RESOURCE_SPECS = (
    ResourceSpec("ApiChangelog", "/", ApiChangelog),
    ResourceSpec("ATC", "/atc-codes", ATC),
    ResourceSpec("Container", "/containers", Container),
    ResourceSpec(
        "ContainerWholesalerRltd",
        "/container-organisation-relationships",
        ContainerWholesalerRltd,
    ),
    ResourceSpec("Copayment", "/copayments", Copayment),
    ResourceSpec("Criteria", "/criteria", Criteria),
    ResourceSpec(
        "CriteriaParameterRltd",
        "/criteria-parameter-relationships",
        CriteriaParameterRltd,
    ),
    ResourceSpec("DispensingRule", "/dispensing-rules", DispensingRule),
    ResourceSpec("ExPrepSfpRltd", "/extemporaneous-prep-sfp-relationships", ExPrepSfpRltd),
    ResourceSpec("ExtemporaneousDrugTariff", "/extemporaneous-tariffs", ExtemporaneousDrugTariff),
    ResourceSpec(
        "ExtemporaneousIngredient", "/extemporaneous-ingredients", ExtemporaneousIngredient
    ),
    ResourceSpec(
        "ExtemporaneousPreparation", "/extemporaneous-preparations", ExtemporaneousPreparation
    ),
    ResourceSpec("Fee", "/fees", Fee),
    ResourceSpec("Indication", "/indications", Indication),
    ResourceSpec("Item", "/items", Item),
    # Opt-in only: excluded from SYNC_ORDER below. Its own fields and every
    # nested array duplicate Item plus 8 already-synced relationship tables
    ResourceSpec("ItemOverview", "/item-overview", ItemOverview),
    ResourceSpec("ItemAmt", "/amt-items", ItemAmt),
    ResourceSpec("ItemAtcRltd", "/item-atc-relationships", ItemAtcRltd),
    ResourceSpec(
        "ItemDispensingRuleRltd",
        "/item-dispensing-rule-relationships",
        ItemDispensingRuleRltd,
    ),
    ResourceSpec(
        "ItemOrganisationRltd",
        "/item-organisation-relationships",
        ItemOrganisationRltd,
    ),
    ResourceSpec(
        "ItemPrescribingTxtRltd",
        "/item-prescribing-text-relationships",
        ItemPrescribingTxtRltd,
    ),
    ResourceSpec("ItemPricingEvent", "/item-pricing-events", ItemPricingEvent),
    ResourceSpec(
        "ItemRestrictionRltd",
        "/item-restriction-relationships",
        ItemRestrictionRltd,
    ),
    ResourceSpec("MarkupBand", "/markup-bands", MarkupBand),
    ResourceSpec("Organisation", "/organisations", Organisation),
    ResourceSpec("Parameter", "/parameters", Parameter),
    ResourceSpec("Prescriber", "/prescribers", Prescriber),
    ResourceSpec("PrescribingTxt", "/prescribing-texts", PrescribingTxt),
    ResourceSpec("Program", "/programs", Program),
    ResourceSpec("ProgramDispensingRules", "/program-dispensing-rules", ProgramDispensingRules),
    ResourceSpec("RestrictionText", "/restrictions", RestrictionText),
    ResourceSpec(
        "RstrctnPrscrbngTxtRltd",
        "/restriction-prescribing-text-relationships",
        RstrctnPrscrbngTxtRltd,
    ),
    ResourceSpec("Schedule", "/schedules", Schedule),
    ResourceSpec(
        "StandardFormulaPreparations",
        "/standard-formula-preparations",
        StandardFormulaPreparations,
    ),
    ResourceSpec("SummaryOfChanges", "/summary-of-changes", SummaryOfChanges),
)

RESOURCE_BY_NAME = {spec.name: spec for spec in RESOURCE_SPECS}
RESOURCE_BY_ENDPOINT = {spec.endpoint: spec for spec in RESOURCE_SPECS}


SYNC_ORDER = (
    "Schedule",
    "Program",
    "Organisation",
    "Container",
    "ATC",
    "DispensingRule",
    "Criteria",
    "Parameter",
    "PrescribingTxt",
    "Indication",
    "Copayment",
    "Fee",
    "RestrictionText",
    "Item",
    "ContainerWholesalerRltd",
    "CriteriaParameterRltd",
    "ExPrepSfpRltd",
    "ItemAtcRltd",
    "ItemDispensingRuleRltd",
    "ItemOrganisationRltd",
    "ItemPrescribingTxtRltd",
    "ItemRestrictionRltd",
    "RstrctnPrscrbngTxtRltd",
    "ItemPricingEvent",
    "ItemAmt",
    "ExtemporaneousDrugTariff",
    "ExtemporaneousIngredient",
    "ExtemporaneousPreparation",
    "StandardFormulaPreparations",
    "MarkupBand",
    "Prescriber",
    "ProgramDispensingRules",
    "SummaryOfChanges",
    "ApiChangelog",
)

if len(SYNC_ORDER) != len(set(SYNC_ORDER)):
    raise RuntimeError("SYNC_ORDER contains duplicate resources")
unknown = sorted(set(SYNC_ORDER) - set(RESOURCE_BY_NAME))
if unknown:
    raise RuntimeError(f"SYNC_ORDER contains unregistered resources: {unknown}")
