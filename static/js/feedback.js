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
    $('#sendFeedbackForm').on('submit', function(e){
        e.preventDefault();
        var $form = $(this);
        var fd = new FormData();
        var other_data = $form.serializeArray();

        $.each(other_data, function(key, input) {
            fd.append(input.name, input.value);
        });

        var notify = $.notify('<strong>Sending....!</strong>...', {
                            allow_dismiss: true,
                            placement: {
                                from: "top",
                                align: "center"
                            },
                        });
        $.ajax({
                type: "POST",
                url: $form.attr('action'),
                data: fd,
                contentType: false,
                processData: false,

                success: function(response) {
                    if (response === "success") {
                        var notify = $.notify('<strong>Your message has been sent!</strong>...', {
                            allow_dismiss: true,
                            placement: {
                                from: "top",
                                align: "center"
                            },
                        });
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
