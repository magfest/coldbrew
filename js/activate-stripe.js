var stripe;
var elements;
var card;

document.addEventListener('DOMContentLoaded', function() {
    stripe = Stripe(apikey);
    elements = stripe.elements();
    card = elements.create('card');
    card.mount('#card-element');
}, false);

function activate_payment() {
    stripe.createToken(card).then(function(result) {
        if (result.error) {
            M.toast({html: result.error.message});
        } else {
            console.log(result.token);
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/accounts/activate", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) {
                    return;
                }
                if (this.status == 200) {
                    var data = JSON.parse(this.responseText);
                    if (data.success) {
                        window.location.href = "/accounts";
                    } else {
                        M.toast({html: data.error});
                    }
                }
                else {
                    M.toast({html: "Failed to add funds: Server returned "+this.status});
                }
            }
            var formEl = document.getElementById("payment-form");
            var formdata = new FormData(formEl);
            var reqdata = {};
            formdata.forEach(function(value, key) {
                reqdata[key] = value;
            });
            reqdata['token'] = result.token.id;
            xhr.send(JSON.stringify(reqdata));
        }
    });
};