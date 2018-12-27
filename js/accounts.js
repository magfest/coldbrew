var modal;

function add_account() {
    console.log("Adding an account!");
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/accounts/create", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) {
            return;
        }
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            if (data.success) {
                modal.close();
                location.reload();
            } else {
                M.toast({html: data.error});
            }
        }
        else {
            M.toast({html: "Failed to create account: Server returned "+this.status});
        }
    }
    var formEl = document.getElementById("accountform");
    var formdata = new FormData(formEl);
    var reqdata = {};
    formdata.forEach(function(value, key) {
        reqdata[key] = value;
    });
    xhr.send(JSON.stringify(reqdata));
}

function open_modal() {
    modal.open();
}

document.addEventListener('DOMContentLoaded', function() {
    var el = document.querySelector('.modal');
    modal = M.Modal.init(el);
});