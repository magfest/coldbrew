function add_cash() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/accounts/activate/cash", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) {
            return;
        }
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            if (data.success) {
                window.location.href = "/accounts";
                M.toast({html: "Funds added successfully."});
            } else {
                M.toast({html: data.error});
            }
        }
        else {
            M.toast({html: "Failed to add funds: Server returned "+this.status});
        }
    }
    var formEl = document.getElementById("cashform");
    var formdata = new FormData(formEl);
    var reqdata = {};
    formdata.forEach(function(value, key) {
        reqdata[key] = value;
    });
    xhr.send(JSON.stringify(reqdata));
}
