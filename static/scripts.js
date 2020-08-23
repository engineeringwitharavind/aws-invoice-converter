// Clear
function clearPage() {
  window.location.reload();
}

// Show Download
function showDownload() {
  document.getElementById("showme").removeAttribute("disabled");
}

// Success Message
function uploadMessage() {
  alert("File(s) Uploaded Successfully!!");
}

// Enabling Buttons - jQuery
$(document).ready(function () {
  $("input:submit").attr("disabled", true);
  $("input:file").change(function () {
    if ($(this).val()) {
      $("input:submit").removeAttr("disabled");
    } else {
      $("input:submit").attr("disabled", true);
    }
  });
});

// Check File Extension
function checkFiles() {
  var fup = document.getElementById("filename");
  var fileName = fup.value;
  var ext = fileName.substring(fileName.lastIndexOf(".") + 1);

  if (ext == "PDF") {
    return true;
  } else {
    alert("Upload PDF Files Only");
    return false;
  }
}
