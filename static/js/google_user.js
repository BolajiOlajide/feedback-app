$(document).ready(function(){
    signOutGoogleUser();
});

$.ajaxSetup({
    headers: {
        "X-CSRFToken": $("meta[name='csrf-token']").attr("content"),
        'Cache-Control': 'no-store'
    },
});
$.ajaxSetup({ cache: false });

function onSignIn(googleUser) {
    console.log("this is google user", googleUser)
    var profile = googleUser.getBasicProfile();
    var id_token = googleUser.getAuthResponse().id_token;
    var url = location.href.split('?');
    var next = url[1]? url[1] : 'next';

    $.ajax({
            type: "GET",
            url: "https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=" + id_token,
            success: function(response) {
                console.log(response)
                $.ajax({
                    type: "GET",
                    url: "/feedback/user/authenticate/" + "?" + next,
                    data: response,

                    success: function(response) {
                        if (response == "success") {
                            location.href= "/feedback/user/home/";
                        }
                    },

                    error: function(error) {
                        console.log(error.responseText);
                        if (error.status == 405) {
                            console.log(error.responseText);
                            signOut();
                        }
                    },

                    headers: {
                        "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val()
                    },
                })
            },

            error: function(error) {
                console.log(error.responseText);
            },
    });

    console.log('id_token: ' + id_token);
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail());

}

function onFailure(error) {
      console.log(error);
}

function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.disconnect().then(function () {
        console.log('User signed out.');
    });
}

function renderButton() {
    gapi.signin2.render('my-signin2', {
        'scope': 'profile email',
        'width': 240,
        'height': 50,
        'longtitle': true,
        'theme': 'dark',
        'onsuccess': onSignIn,
        'onfailure': onFailure
    });
};

function signOutGoogleUser() {
    $('#user-signout').on('click', function(e){
        e.preventDefault();
        $.ajax({
                type: "GET",
                url: "/feedback/user/signout/",

                success: function(response) {
                    if (response === "success") {
                            location.href = "/"
                            signOut();

                        }

                },

                error: function(error) {
                        console.log(error.responseText)
                },
        });
    });
}
