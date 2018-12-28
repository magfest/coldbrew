var modal;
var delmodal;
var to_delete;

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

function delete_account(name, id) {
    to_delete = {name: name, id: id};
    var el = document.querySelector('.delete-title');
    el.innerHTML = "<h4>Delete Account: " + name + "</h4>"
    delmodal.open();
}

function confirm_delete() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/accounts/delete", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) {
            return;
        }
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            if (data.success) {
                delmodal.close();
                M.toast({html: "Account deleted successfully."})
                location.reload();
            } else {
                M.toast({html: data.error});
            }
        }
        else {
            M.toast({html: "Failed to delete account: Server returned "+this.status});
        }
    }
    xhr.send(JSON.stringify({managed_account: to_delete.id}));
}

document.addEventListener('DOMContentLoaded', function() {
    var el = document.querySelector('#account-modal');
    modal = M.Modal.init(el);
    var delel = document.querySelector('#delete-modal');
    delmodal = M.Modal.init(delel);
});