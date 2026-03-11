// Using Django's built-in jQuery for admin
(function ($) {
  $(document).ready(function () {
    const categorySelect = $("#id_category");
    if (!categorySelect.length) {
      return; // Exit if the category field isn't on this page
    }

    const bhkRow = $(".field-bhk");
    const bhkLabel = bhkRow.find("label");
    const bhkInput = $("#id_bhk");
    const bhkHelpText = bhkRow.find(".help");

    const originalBhkLabel = "BHK:";
    const originalBhkHelpText =
      "BHK options for Residential, e.g., '2 BHK, 3 BHK'. Use commas to separate.";
    const commercialSqrtLabel = "Area (Sq. Ft.):";
    const commercialSqrtHelpText =
      "Enter numbers for square footage (e.g., 500, 1250.5). 'Sq. Ft.' is added automatically. Use commas for multiple values.";

    function updateBhkField() {
      if (categorySelect.val() === "COMMERCIAL") {
        bhkLabel.text(commercialSqrtLabel);
        bhkHelpText.text(commercialSqrtHelpText);
      } else {
        bhkLabel.text(originalBhkLabel);
        bhkHelpText.text(originalBhkHelpText);
      }
    }

    function formatSqrtInput() {
      if (categorySelect.val() !== "COMMERCIAL") {
        return;
      }

      let value = bhkInput.val().trim();
      if (!value) {
        return;
      }

      // Process comma-separated values
      const parts = value.split(",").map((part) => {
        let cleanPart = part
          .trim()
          .replace(/sq\.? ?ft\.?/gi, "")
          .trim();

        // Check if it's a valid positive number (int or float)
        if ($.isNumeric(cleanPart) && parseFloat(cleanPart) >= 0) {
          return cleanPart + " Sq. Ft.";
        } else if (cleanPart) {
          return part.trim(); // Preserve non-numeric values
        }
        return ""; // Discard empty parts
      });

      bhkInput.val(parts.filter((p) => p).join(", "));
    }

    // Run on page load to set the correct initial state
    updateBhkField();

    // Run on category change
    categorySelect.on("change", updateBhkField);

    // Add formatting on blur for the SQRT field
    bhkInput.on("blur", formatSqrtInput);
  });
})(django.jQuery);
