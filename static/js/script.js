const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("user-input");

$(document).ready(function () {
  $(".btn.disabled, .grade").toggle();
});

$("[id^=grade]").on("click", function () {
  let btn = $(this);
  btn.toggle();
  btn.siblings(".btn").toggle();
  fetch("/get_grade?qid=" + btn.data("qid"), {
    method: "get",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data[0].answer) {
        $(
          `<h5 class="card-title">GradeGPT says</h5>
          <div>${data[0].score}</div>
          <div class="mt-2">${data[0].answer}</div>`
        ).appendTo("div[data-gradeId=" + btn.data("qid") + "]");
      } else {
        $(`<h5 class="card-title">No answer found! Please try again</h5>`);
      }
      btn.toggle();
      btn.siblings(".btn").toggle();
    })
    .catch((error) => {
      console.error("Error:", error);
    });
});

$("#user-input").keyup(function (event) {
  if (event.keyCode === 13) {
    $("#sendMessageBtn").click();
  }
});

function sendMessage() {
  const userMessage = userInput.value;
  displayMessage("You", userMessage, "sent");
  userInput.value = "";

  // Make an API call to the Flask backend to get the chatbot response
  fetch("/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `user_input=${userMessage}`,
  })
    .then((response) => response.json())
    .then((data) => {
      displayMessage("GradeGPT", data.message, "received");
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function displayMessage(sender, message, messageType) {
  const messageElement = document.createElement("div");
  messageElement.classList.add("message", messageType);
  messageElement.innerHTML = `<span><b>${sender}:</b> ${message}</span>`;
  chatbox.appendChild(messageElement);
  chatbox.scrollTop = chatbox.scrollHeight;
}

// ----------multiplefile-upload---------
$("#multiplefileupload").fileinput({
  theme: "explorer",
  uploadUrl: "/upload",
  hideThumbnailContent: true, // hide image, pdf, text or other content in the thumbnail preview
  minFileCount: 2,
  removeFromPreviewOnError: true,
  overwriteInitial: false,
  previewFileIcon: '<i class="fas fa-file"></i>',
  fileActionSettings: {
    showUpload: false,
    showZoom: false,
    showDrag: true,
    dragIcon: '<i class="bi bi-arrows-move"></i>',
  },
  // uploadUrl: "#",
  // deleteUrl: "#",
  // initialPreviewAsData: false,
  // overwriteInitial: false,
  // dropZoneTitle: '<div class="upload-area"><i class="bi bi-cloud-arrow-up-fill"></i><p>Browse or Drag and Drop .docx</p> <div> <button class="btn btn-futuristic">Browse File</button> </div></div>',
  // dropZoneClickTitle: "",
  // browseOnZoneClick: true,
  // showRemove: false,
  // showUpload: false,
  // showZoom: false,
  // showCaption: false,
  // showBrowse: false,
  // browseClass: "btn btn-danger",
  // browseLabel: "",
  // browseIcon: "<i class='fa fa-plus'></i>",
  // fileActionSettings: {
  //     showUpload: false,
  //     showDownload: false,
  //     showZoom: false,
  //     showDrag: true,
  //     removeIcon: "<i class='bi bi-x-lg'></i>",
  //     uploadIcon: '<i class="bi bi-cloud-arrow-up-fill"></i>',
  //     dragIcon: '<i class="bi bi-arrows-move"></i>',
  //     uploadRetryIcon: '<i class="bi bi-arrow-clockwise"></i>',
  //     dragClass: "file-drag",
  //     removeClass: "file-remove",
  //     removeErrorClass: 'file-remove',
  //     uploadClass: "file-upload",
  // },
  // frameClass: "file-sortable",
  // layoutTemplates: {
  //     preview:
  //         '<div class="file-preview {class}">\n' +
  //         '    <div class="{dropClass}">\n' +
  //         '    <div class="clearfix"></div>' +
  //         '    <div class="file-preview-status text-center text-success"></div>\n' +
  //         '    <div class="kv-fileinput-error"></div>\n' +
  //         "    </div>\n" +
  //         "</div>" +
  //         ' <div class="file-preview-thumbnails">\n' +
  //         " </div>\n",
  //     actionDrag: '<button class="file-drag-handle {dragClass}" title="{dragTitle}">{dragIcon}</button>',
  //     footer: '<div class="file-thumbnail-footer">\n' + '<div class="file-detail">' + '<div class="file-caption-name">{caption}</div>\n' + '    <div class="file-size">{size}</div>\n' + "</div>" + "   {actions}\n" + "</div>",
  // },
});

$("#multiplefileupload").on("fileuploaded", function (event, data) {
  location.href = appUrl + "/grade";
});
