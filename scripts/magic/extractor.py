import json
from typing import Optional, Literal

import dspy

# ----------------------------------------------------------------------------------------
#   PYDANTIC MODELS
# ----------------------------------------------------------------------------------------


class ProductCategoryClassification(dspy.Signature):
    """Classify electronic product category of a given description."""

    description: str = dspy.InputField()
    category: Literal["LAPTOP", "COMPUTER", "OTHER"] = dspy.OutputField()


class LaptopSpecification(dspy.Signature):
    """Extracts laptop technical specification."""

    description: str = dspy.InputField()
    additional_description: Optional[str] = dspy.InputField(
        desc="Additional product information if the provided description cannot provide enough information. Use this as last resort."
    )

    brand: Optional[str] = dspy.OutputField(
        desc="Brand or manufacturer, for example: Acer, ASUS, Merdeka, Libera, Lenovo, MSI, SPC, etc. If the product has 'MyBook' or 'My Book' in it, it must be AXIOO. If the device has no recognizable brand, return UNKNOWN.",
    )
    series_model: Optional[str] = dspy.OutputField(
        description="Laptop series and model or type",
    )
    processor: Optional[str] = dspy.OutputField(
        desc="Processor or CPU brand, model number, generation, and capabilities."
    )
    memory: Optional[str] = dspy.OutputField(
        desc="Total memory or RAM. If the unit measurement is not provided, assume it's in GB."
    )
    storage: Optional[str] = dspy.OutputField(
        desc="Total disk storage including hard drives, SSDs, and other mass storage devices. If the unit measurement is not provided, assume it's in GB.",
    )
    graphics_card: Optional[str] = dspy.OutputField(
        desc="Graphics card or GPU name, for example: Nvidia RTX 3060, Intel UHD Graphics, etc.",
    )


# ----------------------------------------------------------------------------------------
#   EXTRACTORS
# ----------------------------------------------------------------------------------------


class StructuredDataExtractor:
    def __init__(self, fewshot_file: str):
        # create prompter for laptop spec extraction
        self.spec_extractor = dspy.ChainOfThought(LaptopSpecification)

        # create prompter for product classifier
        with open(fewshot_file, "r") as f:
            # read few-shot prompt sample
            trainset = [
                dspy.Example(**json.loads(x)).with_inputs("description", "reasoning")
                for x in f
                if len(x.strip()) > 1
            ]

            # create COT classifier
            classify = dspy.ChainOfThoughtWithHint(ProductCategoryClassification)
            optimizer = dspy.LabeledFewShot()

            self.product_category_classif = optimizer.compile(
                classify, trainset=trainset
            )

    def extract_product_type(self, description: str) -> str:
        res = self.product_category_classif(description=description)
        return res.category

    def extract_specs(self, description: str, additional_description: str):
        return self.spec_extractor(
            description=description, additional_description=additional_description
        )
