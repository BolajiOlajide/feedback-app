$(document).ready(function(){
    sendFeedback();
});

$.ajaxSetup({
    headers: {
        "X-CSRFToken": $("meta[name='csrf-token']").attr("content"),
        'Cache-Control': 'no-store'
    },
});
$.ajaxSetup({ cache: false });

function sendFeedback() {
    var fd = new FormData();
    var file_data = $form.find('input[type="file"]')[0].files[0];
    var other_data = $form.serializeArray();

    $.each(other_data, function(key, input) {
        fd.append(input.name, input.value);
    });

    $('#sendFeedbackForm').on('submit', function(e){
        e.preventDefault();
        $.ajax({
                type: "POST",
                url: $form.attr('action'),
                data: fd,
                contentType: false,
                processData: false,

                success: function(response) {
                    if (response === "success") {
                            console.log("TO DO::: Bootstrap notifier")

                        }

                },

                error: function(error) {
                        console.log(error.responseText)
                },

                headers: {
                        "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()
                    },
        });
    });
}
