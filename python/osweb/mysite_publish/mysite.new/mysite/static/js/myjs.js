$(function() {
        var hit = 10; // 显示的下拉提示列表的长度，可修改
         
        setTimeout(function() {
            $( "#searchBox" ).autocomplete({
                delay: 0,
                source: function(request, response) {
                    $.ajax({
                        url: 'http://localhost:8999/suggest/',
                        xhrFields: {
                            withCredentials: true
                        },
                        dataType: 'json',//如果需要为jsonp类型，则需要在下面的data属性中加上callback: ?
                        data: {keywords: $( "#searchBox" ).val()},
                        success: function(data) {
                            if(data.status === 'OK' && data.result) {
                                if(data.result.length >= hit) {
                                    response(data.result.slice(0, hit));
                                } else {
                                    response(data.result);
                                }
                            } else if( data.status === 'FAIL' && data.errors ){
                                alert(data.errors[0].message);
                            }
                        }

                    });
                }
            }).bind("input.autocomplete", function () {
                // 修复在Firefox中不支持中文的BUG
                $( "#searchBox" ).autocomplete("search", $( "#searchBox" ).val());
            }).focus();
        }, 0);
    });
