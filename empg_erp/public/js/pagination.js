var Pagination = function (){

    this.pagination_arr = [],
    this.totalPages = 0,
    this.paginationSize = 7,
    this.paginateLimit = [20,100,500],
    this.currentPage = 1,
    this.totalRecords = "",

    this.append_pagination = function (){
        $('div[data-fieldname="page"]').hide();

        var html = '<div class="pagination pull-right">'+
                        '<li id="previous-page" class="page-item">'+
                            '<a class="page-link" href="javascript:;" tabindex="-1">Previous</a>'+
                        '</li>'+
                        '<li id="next-page" class="page-item">'+
                            '<a class="page-link" href="javascript:;" tabindex="-1">Next</a>'+
                        '</li>'+
                    '</div>';
        $('.pagination').remove();
        $('.layout-footer').after(html);

        return this.showPage();

    },
    // api url, function ref, filters, pageNo

    this.getPageList = function (page, maxLength) {
        if (maxLength < 5) throw "maxLength must be at least 5";

        function range(start, end) {
            return Array.from(Array(end - start + 1), (_, i) => i + start);
        }

        var sideWidth = maxLength < 9 ? 1 : 2;
        var leftWidth = (maxLength - sideWidth*2 - 3) >> 1;
        var rightWidth = (maxLength - sideWidth*2 - 2) >> 1;
        if (this.totalPages <= maxLength) {
            // no breaks in list
            return range(1, this.totalPages);
        }
        if (page <= maxLength - sideWidth - 1 - rightWidth) {
            // no break on left of page
            return range(1, maxLength-sideWidth-1)
                .concat([0])
                .concat(range(this.totalPages-sideWidth+1, this.totalPages));
        }
        if (page >= this.totalPages - sideWidth - 1 - rightWidth) {
            // no break on right of page
            return range(1, sideWidth)
                .concat([0])
                .concat(range(this.totalPages - sideWidth - 1 - rightWidth - leftWidth, this.totalPages));
        }
        // Breaks on both sides
        return range(1, sideWidth)
            .concat([0])
            .concat(range(page - leftWidth, page + rightWidth))
            .concat([0])
            .concat(range(this.totalPages-sideWidth+1, this.totalPages));
    },

    this.showPage = function() {
        let whichPage = this.currentPage;
        
        this.totalPages = this.pagination_arr.length;
        if (whichPage < 1 || whichPage > this.totalPages) return false;
        this.currentPage = whichPage;
        // Replace the navigation items (not prev/next):
        $(".pagination li:not('#next-page,#previous-page')").remove();

        this.getPageList(this.currentPage, this.paginationSize).forEach( item => {
            $("<li>").addClass("page-item")
                    .addClass(item ? "current-page" : "disabled")
                    .toggleClass("active", item === this.currentPage).append(
                $("<a>").addClass("page-link").attr({
                    href: "javascript:void(0)"}).text(item || "...")
            ).insertBefore("#next-page");
        });
        // Disable prev/next when at first/last page:
        $("#previous-page").toggleClass("disabled", this.currentPage == 1);
        $("#next-page").toggleClass("disabled", this.currentPage == this.totalPages);
        return true;
    },

    this.hideDefaultFilter = function(){
        $('div[data-fieldname="page"]').hide();
    },

    this.append_limit = function(){
        var html = '<div class="list-paging-area paging-limit level">'+
                        '<div class="level-left">'+
                            '<div class="btn-group">';
                            $.each(this.paginateLimit,function(index,element){
                                html +='<button type="button" class="btn btn-default custom-report-limit btn-sm btn-paging" data-value="'+element+'">'+element+'</button>';
                            });
                            html +='</div>'+
                        '</div>'+
                        '<div class="level-right">'+
                            '<button class="btn btn-default btn-more btn-more-paging btn-sm">More...</button>'+
                        '</div>'+
                    '</div>';
        return html;
    },

    this.show_limit_paging = function(){
        $('.paging-limit').remove();
        $('.layout-footer').after(this.append_limit());
        var page = $('#page').val();
        if(page == "" || page == undefined){
            page = 20+"_";
        }
        page = page.split("_");
        var selected_value = page[0]
        if(page[1] != "" && page[1] !=undefined)
            selected_value = page[1]
        $('.btn-more-paging').show();
        if(this.totalRecords <= page[0])
            $('.btn-more-paging').hide();
        $('.custom-report-limit[data-value= "'+selected_value+'"]').addClass('btn-info');
    }


}

$(function(){
    window.pagination = new Pagination();
});
// Use event delegation, as these items are recreated later
$(document).on("click", ".pagination li.current-page:not(.active)", function () {
    window.pagination.currentPage = +$(this).text();
    $('select[data-fieldname="page"]').val(window.pagination.currentPage).trigger('change');
    return window.pagination.showPage();
});
$(document).off('click',"#next-page").on("click","#next-page", function () {
    window.pagination.currentPage = window.pagination.currentPage+1;
    if (window.pagination.currentPage > window.pagination.totalPages) return false;
    $('select[data-fieldname="page"]').val(window.pagination.currentPage).trigger('change');
    return window.pagination.showPage();
});
$(document).off('click',"#previous-page").on("click","#previous-page", function () {
    window.pagination.currentPage = window.pagination.currentPage-1;
    if (window.pagination.currentPage < 1 ) return false;
    $('select[data-fieldname="page"]').val(window.pagination.currentPage).trigger('change');
    return window.pagination.showPage();
});

/******************** Pagination limit Implementation*********************/

$(document).off('click','.custom-report-limit:not(".btn-info")').on('click','.custom-report-limit:not(".btn-info")',function(){
    var value = $(this).attr('data-value');
    $('.custom-report-limit').removeClass('btn-info');
    $(this).addClass('btn-info');
    $('select[data-fieldname="page"]').val(value).trigger('change');
    return;
});

$(document).off('click','.btn-more-paging').on('click','.btn-more-paging',function(){
    var value = $('.custom-report-limit.btn-info').attr('data-value');
    var page = $('#page').val();
    page = page.split("_")[0];
    var total = parseInt(value)+parseInt(page);
    $('.last-page-option').remove();
    $('select[data-fieldname="page"]')
         .append($("<option></option>")
                    .attr({
                        "value":total+'_'+value,
                        "class":"last-page-option"
                     }).text(total));

    $('select[data-fieldname="page"]').val(total+'_'+value).trigger('change');
    return;
});

/******************** Pagination limit Implementation*********************/
