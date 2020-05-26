/* Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

odoo.define('website_advanced_wishlist.website_advanced_wishlist', function(require) {
    "use strict";
    var ajax = require('web.ajax');
    var base = require('web_editor.base');
    var core = require('web.core');
    var utils = require('web.utils');
    var _t = core._t;
    var website_sale_utils = require('website_sale.utils');
    
    var default_wishlist_id;
    var current_wishlist_id=false;
    var selected_wishlist_id=false;
    var current_product_id=false;
    var $current_heart_element;
    var add_to_wishlist_action = "show";
    var last_product=false;
    var product_ids_in_wish=[];
   
    $(document).ready(function() {
        var p_ids_i_w = $("#product_details").find("input.product_ids_in_wish").val()
        if (p_ids_i_w)
            product_ids_in_wish=$.parseJSON(p_ids_i_w);
            
        get_default_wishlist_id();
        var nameReg = /^[A-Za-z]/;

        $('#wishlist_input').focus(function(){
            $('#wishlist_input').addClass("wishlist_input_normal").removeClass("wishlist_input_error");
            $('.wishlist_modal_error_msg').addClass('wishlist_modal_msg').removeClass('wishlist_modal_error_msg').text("create a new wishlist category here!");
            $('.popover_input').removeClass('wishlist_input_error').val('').css('color','#555555');
        }); 
        $(document).on('click','.wishlist_popover',function(e){
            e.stopPropagation();
        });
        $(document).on('click','.container, #wrapwrap' ,function(e){
            $('.wishlist_popover').hide();
            $(".wishlist_tab_menu").hide();
            $('.move_to_wishlist_dropdown').hide();
            $('.wishlist_header_menu_icon span').removeClass('clicked');
            $('.wishlist_tab_menu_icon').removeClass('clicked');
            $('.move_to_wishlist').removeClass('clicked');
            $('.add_to_wishlist_heart_icon').removeClass('clicked');
            $('.add_to_wishlist_dropdown').removeClass('clicked');
            $('.add_to_wishlist_button').removeClass('clicked'); 
        });
        $(document).on('click','.popover_wishlist_name',function(){
            selected_wishlist_id=$(this).attr('name_id');
        });    
        $(document).on('click','.add_to_wishlist_heart_icon',function(e){
            e.stopPropagation();
            current_product_id= parseInt($(this).data('product-product-id'), 10);
            $current_heart_element = $(this);
            
            if(add_to_wishlist_action=="default"){
                if($current_heart_element.hasClass('black_heart_icon')){
                    if(default_wishlist_id){
                        add_product_to_wishlist($current_heart_element);
                    }else{
                        reload_popover_wishlists();        
                    }
                    
                }else if($current_heart_element.hasClass('white_heart_icon')){
                    remove_from_wishlist($current_heart_element);
                }
                    
            }else if(add_to_wishlist_action=="show"){
                reload_popover_wishlists();
            }
            else{
                alert("something went wrong");
            }   
        });
        $(document).on('click','.wishlist_popover_close' ,function(e){
            $('.wishlist_popover').hide();
            $current_heart_element.removeClass('clicked');
        });

        $(document).on('click', '#create_new_wishlist', function(ev) {
            $('#wishlist_input').removeClass("wishlist_input_error").addClass("wishlist_input_normal").val("");
            $("#default_wishlist_checkbox_create").prop("checked",false);
            $('.wishlist_modal_error_msg').text('create a new wishlist category here!');
            $('.wishlist_modal_error_msg').addClass('wishlist_modal_msg').removeClass('wishlist_modal_error_msg');
            
        });

        $(document).on('click', '#create_wishlist_button', function(ev) {
            ev.stopPropagation();
            var name = $("#wishlist_input").val();
            if (!name||!nameReg.test(name)){
                $('#wishlist_input').removeClass("wishlist_input_normal").addClass("wishlist_input_error");
            }
            else{
                 create_wishlist(name);   
            }
            
        });
        $(document).on('click', '#create_wishlist_link', function(ev) {
            $('#wishlist_input').removeClass("wishlist_input_error").addClass("wishlist_input_normal").val("");
            $('#wishlist_inputs').show();
            $('#create_wishlist_link').hide();
            
            
        });
        $(document).on('click', '#cancle_wishlist_button', function(ev) {
            $('#wishlist_inputs').hide();
            $('#create_wishlist_link').show();
        });

        $(document).on('click', '.add_product_to_wishlist', function(ev) {
            selected_wishlist_id=$(this).attr('name_id');
            add_product_to_wishlist($(this));
        });

        $(document).on('click', '.remove_from_wishlist,.remove_from_wishlist_icon', function(ev) {
            ev.stopPropagation();
            last_product = $(this).attr("last");
            remove_from_wishlist($(this));
        });
        
        $(document).on('click', '.wishlist_tap', function(ev) {
            var name_id = $(this).attr("name_id");
            current_wishlist_id=name_id;
            selected_wishlist_id=name_id;

            $(".wishlist_tap ").removeClass("wishlist_tap_selected");
            $("#wishlist_tab_link_"+selected_wishlist_id).addClass("wishlist_tap_selected");
            
            $(".wishlist_tab_content").addClass("hidden");
            $("#wishlist_tab_content_"+selected_wishlist_id).removeClass("hidden");
                     
        });
        $(document).on('click', '.wishlist_header_menu_icon span', function(e) {
            e.stopPropagation();
            var name_id = $(this).attr("name_id");
            current_wishlist_id=name_id;
            var p=$(this).position();
            $(".wishlist_tab_menu").css('top', p.top+18+"px").css('left',p.left-146+'px');
            
            if($(this).hasClass('clicked')){
                $(".wishlist_tab_menu").hide();
                $(this).removeClass('clicked');
            }else{
                $('.wishlist_header_menu_icon span').removeClass('clicked');
                $(".wishlist_tab_menu_icon").removeClass('clicked');
                $(this).addClass('clicked');
                $(".wishlist_tab_menu").show();
            }
            remove_menu_item();
                     
        });
        function remove_menu_item(){
            if( ($("#wishlist_default_dot_"+current_wishlist_id).css('visibility')).toLowerCase() == 'visible') 
                {$('#make_it_default_menu').hide();}
            else
                {$('#make_it_default_menu').show();}

            if( $("#tab_menu_product_count_"+current_wishlist_id).html() == '0 Product(s)')
                {$('#move_wishlist_to_cart').hide();}
            else
                {$('#move_wishlist_to_cart').show();}
        }
        
        $(document).on('click', '.wishlist_tab_menu_icon', function(e) {
            e.stopPropagation();
            var h= $(this).height();
            var p=$(this).position();
            var name_id = $(this).attr("name_id");
            current_wishlist_id=name_id;
            $(".wishlist_tab_menu").css('top',p.top+h*2+'px').css('left',p.left-p.left*1.11+'px');
            
            if($(this).hasClass('clicked')){
                $(".wishlist_tab_menu").hide();
                $(this).removeClass('clicked');
            }else{
                $(".wishlist_tab_menu_icon").removeClass('clicked');
                $('.wishlist_header_menu_icon span').removeClass('clicked');
                $(this).addClass('clicked');
                $(".wishlist_tab_menu").show();
            }
            remove_menu_item();            
        });
        $(document).on('click', '#wishlist_edit_menu', function(e) {
            e.stopPropagation();
            $("#wishlist_edit_input").val($.trim($("#wishlist_products_header_"+current_wishlist_id).text())).removeClass("wishlist_input_error").addClass("wishlist_input_normal");
            $("#default_wishlist_checkbox_edit").prop("checked",false);
            $('.wishlist_modal_error_msg').text('Edit your wishlist here! and save the changes');
            $('.wishlist_modal_error_msg').addClass('wishlist_modal_msg').removeClass('wishlist_modal_error_msg');
            $("#edit_wishlist_modal").modal("show");
        });
        $(document).on('click', '#delete_wishlist_menu', function(ev) {
            $("#confirmation_checkbox").prop("checked",false);
            $('#warning_wishlist_modal').modal('show');
            $('#modal_wishlist_name').html($('#wishlist_products_header_'+current_wishlist_id).text());
        });

        $(document).on('click', '#delete_wishlist_button', function(ev) {
            var tab_menu = $('#wishlist_tab_link_'+current_wishlist_id);
            var tab_content = $('#wishlist_tab_content_'+current_wishlist_id);
            
            if ($("#confirmation_checkbox").is(":checked")) {

                ajax.jsonRpc('/remove/wishlist/'+current_wishlist_id+'/', 'call', {
                }).then(function(data) {
                    if(data.res){
                        $('#warning_wishlist_modal').modal('hide'); 
                        $('#wishlist_notify_save').html(  "SUCCESS! Wish List Deleted").fadeIn().delay(2000).fadeOut();
                        $('.wishlist_tab_content').find('#dropdown_wishlist_'+current_wishlist_id).remove();
                        
                        if(selected_wishlist_id==current_wishlist_id){
                            selected_wishlist_id=default_wishlist_id;
                        }
                        if(current_wishlist_id==default_wishlist_id){
                            selected_wishlist_id=data.name_id;
                        }
                           
                        default_wishlist_id=data.name_id;
                        tab_menu.fadeOut(1000,function(){tab_menu.remove();});
                        tab_content.fadeOut(1000,function(){tab_content.remove();});
                        reload_tab_view();
                    }else{ 
                        console.log("wishlist not Deleted");
                    }  
                });    
            }else{
                $(".checkmark").addClass("highlite_checkbox");setTimeout(() => {
                    $(".checkmark").removeClass('highlite_checkbox');
                },1000 );
            } 
        });

        $(document).on('click', '#make_it_default_menu', function(ev) {
            make_it_default_wishlist(current_wishlist_id);    
        });
        $(document).on('click', '#save_wishlist_button', function(ev) {
            var name_id= current_wishlist_id;
            var name = $("#wishlist_edit_input").val();
            var wishlist_names=[];
            $(".tab_menu_wishlist_name").each(function(){
                var w_name= $(this).find('span').text();
                wishlist_names.push(w_name);
            });
            if (!name||!nameReg.test(name)){
                $('#wishlist_edit_input').removeClass("wishlist_input_normal").addClass("wishlist_input_error");
            }else if ($.inArray(name,wishlist_names)!=-1){
                $('#wishlist_edit_input').removeClass("wishlist_input_normal").addClass("wishlist_input_error");
                show_modal_error_msg("wishlist already exists with this name");
            }else{
                ajax.jsonRpc('/save/wishlist/'+name_id+'/','call',{
                                'name':name
                }).then(function(res){
                    if (res){
                        $('#wishlist_notify_save').html(  "SUCCESS! Wish List Saved ").fadeIn().delay(2000).fadeOut();
                        $("#wishlist_products_header_"+name_id).html(name);
                        $("#tab_menu_wishlist_name_"+name_id).html(name);
                        $('#dropdown_wishlist_'+name_id+' span').text(name);
                        $("#edit_wishlist_modal").modal( 'hide');

                        if($("#default_wishlist_checkbox_edit").is(":checked")){
                            make_it_default_wishlist(name_id);
                            
                        }
                    }
                });
            }    
        });
        
        $(document).on("click", "#move_wishlist_to_cart", function(ev) {
            
            ajax.jsonRpc("/shop/wishlist/cart/move/"+current_wishlist_id+"/", 'call', {
            }).then(function(orders){
                var i;
                for(i=0;i<orders.length;i++){
                    var $q = $(".my_cart_quantity");
                    if (orders[i].cart_quantity) {
                        $q.parent().parent().removeClass("hidden");
                    } else {
                        $q.parent().parent().addClass("hidden");
                        $('a[href^="/shop/checkout"]').addClass("hidden")
                    }
                    $q.html(orders[i].cart_quantity).hide().fadeIn(600);
                }
                // update_wishlist_products(name_id);
                selected_wishlist_id=current_wishlist_id;
                reload_tab_view();
            });
        });

        $(document).on("click", ".move_to_cart", function(ev) {
            var name_id =$(this).attr("name_id");  
            var row = $(this).closest('tr');
            var product_id = parseInt(row.find('.product_id').val(), 10); 
            var value = 1;
            var $input = $(this);
            last_product = $(this).attr("last");
            if ($input.data('update_change')) {
                return;
            }
            ajax.jsonRpc("/shop/cart/update_json", 'call', {
                'line_id': NaN,
                'product_id': product_id,
                'add_qty': value
            })
            .then(function(data) {
                remove_from_wishlist($input);
                $input.data('update_change', false);
                if (value !== 1) {
                    $input.trigger('change');
                    return;
                }
                var $q = $("li#my_cart");
                if (data.cart_quantity) {
                    $q.removeClass("d-none");
                } else {
                    $q.addClass("d-none");
                    $('a[href^="/shop/checkout"]').addClass("hidden")
                }
                $q.find(".my_cart_quantity").html(data.cart_quantity).hide().fadeIn(600);
                if(last_product)
                    window.location.reload(); 
            });        
        });
        $(document).on('click','.move_to_wishlist',function(e){
            e.stopPropagation();
            current_wishlist_id=$(this).attr("name_id");
            selected_wishlist_id=current_wishlist_id;
            current_product_id = $(this).attr("product_id");
            last_product = $(this).attr("last");
            var p = $(this).position();
            $('.move_to_wishlist_dropdown').css('top',p.top+45+'px');
            
            if($(this).hasClass('clicked')){
                $(".move_to_wishlist_dropdown").hide();
                $(this).removeClass('clicked');
            }else{
                $(".move_to_wishlist").removeClass('clicked');
                $(this).addClass('clicked');
                $(".move_to_wishlist_dropdown").show();
            }
            $('.move_to_wishlist_selected').show();
            $(this).parents('#wishlist_tab_content_'+current_wishlist_id).find('#dropdown_wishlist_'+current_wishlist_id).hide();

        });
        $(document).on('click', '.move_to_wishlist_selected', function(ev) {  
            var move_to_wishlist_id = $(this).attr("name_id");
            move_to_wishlist(current_product_id,current_wishlist_id,move_to_wishlist_id);
        });

        $(document).on('click', '.add_to_wishlist_button', function(ev) {
            ev.stopPropagation();
            $current_heart_element=$(this);
	        var p= $(this).position();
            $('.wishlist_popover').css('top', p.top+66 + 'px').css('left', p.left + 'px');
            selected_wishlist_id=false;
            if($(this).hasClass('added_to_wishlist')|| !default_wishlist_id){
                reload_popover_wishlists();
            }else{
                if(default_wishlist_id){
                    $('.product_page_status').css('top',$(this).position().top+66+'px');
                    add_product_to_wishlist($current_heart_element);
                }
            }
        });
        $(document).on('click', '.add_to_wishlist_dropdown', function(ev) {
            ev.stopPropagation();
            // current_product_id=$(this).parents("#product_details").find("input[name='product_id'].product_id").val();
            $current_heart_element=$(this);
            var p= $(this).position();
            $('.wishlist_popover').css('top', p.top+66 + 'px').css('left', p.left-204 + 'px');
            reload_popover_wishlists();
            
        });
        $("#product_details").on('change', 'input.product_id', function(ev) {
            current_product_id=parseInt($(this).val());
            if ($.inArray(current_product_id, product_ids_in_wish) != -1) {
                added_to_wishlist_button();
            } else {
                add_to_wishlist_button();
            }
            // var p= $(this).position();
            // $('.wishlist_popover').css('top', p.top+66 + 'px').css('left', p.left-204 + 'px');
            // reload_popover_wishlists();
            
        });

    });

    function reload_popover_wishlists(){
        $.get("/get/popover/wislists/",{'product_id':current_product_id},function(data) {
            $('.wishlist_popover_wishlists').html(data).scrollTop(0,0);
            show_wishlist_popover();
        });
    } 
    function show_wishlist_popover(){
        $('#wishlist_inputs').hide();
        $('#create_wishlist_link').show();
        if($current_heart_element.hasClass('add_to_wishlist_heart_icon')){
            var element_height =$('.wishlist_popover').height();
            var element_width=$('.wishlist_popover').width();
            var wh = $(window).height();
            var ww =$(window).width();
            var scrollTop =$(window).scrollTop();
            var p = $current_heart_element.offset();
            var realX;
            var realY;
            if(p.top+element_height> wh+scrollTop){
                if($('#oe_main_menu_navbar').length==0){realY=p.top-element_height;}else{realY=p.top-19-element_height;}
                if(p.left+element_width>ww){realX=p.left-element_width-30;}else{realX=p.left+25;}
            }
            else{
                if(p.left+element_width>ww){realX=p.left-element_width-30;}else{realX=p.left+25;}
                if($('#oe_main_menu_navbar').length==0){realY=p.top;}else{realY=p.top-36;}
                
            }
            $('.wishlist_popover').css('top',realY + 'px').css('left', realX + 'px');
        }    
        
        if($($current_heart_element).hasClass('clicked')){
            $('.wishlist_popover').hide();
            $($current_heart_element).removeClass('clicked');
        }else{
            $('.add_to_wishlist_heart_icon').removeClass('clicked');
            $($current_heart_element).addClass('clicked');
            $('.wishlist_popover').show();
        }
    }
    
    function create_wishlist(input){
        // make_it_default variabel is globaly define
        var make_it_default = false;

        if($("#default_wishlist_checkbox_create").is(":checked")){
            make_it_default = true;
        }else{make_it_default=false;}
        
        ajax.jsonRpc("/shop/create/wislist/",'call',{"name":input,"make_it_default":make_it_default,"product_id":current_product_id})
        .then(function(data) {
            if (data){
              
                if($('.wishlist_popover_wishlists')){
                    if(add_to_wishlist_action=="default"){
                        $('.added_to_default_status span:nth-child(3)').text($('#wishlist_input').val());
                    }
                    $('#wishlist_input').val("");
                    $('#wishlist_notify_save').html("SUCCESS! Wish List '"+input+"' is Created!!").fadeIn().delay(2000).fadeOut();                 
                    $("#create_wishlist_modal").modal("hide");
                    if(!default_wishlist_id){get_default_wishlist_id();}
                    selected_wishlist_id=data.name_id;
                    if(window.location.pathname!="/wishlists/"){
                            add_product_to_wishlist()
                    }else{  
                        // $('.wishlist_popover_wishlists').html(data.html);
                        reload_tab_view();
                    }
                    
                }
            }else{
                show_modal_error_msg("wishlist already exists with this name");
             
            }
            
        });
    }
    function show_modal_error_msg(msg){
        $('.wishlist_modal_msg').text(msg);
        $('.wishlist_modal_msg').removeClass('wishlist_modal_msg').addClass('wishlist_modal_error_msg');
        $('.popover_input').addClass("wishlist_input_error").val("wishlist already exists").css('color','#FF4F4F');
        $('#wishlist_input').addClass('wishlist_input_error');setTimeout(() => {
                $('.popover_input').removeClass('wishlist_input_error').val('').css('color','#555555');
                $('#wishlist_input').removeClass('wishlist_input_error');
        },4000 );
    }
       
    function make_it_default_wishlist(name_id){
        
        ajax.jsonRpc('/wishlist/set_as_default/', 'call', {
                         "name_id":name_id,
        }).then(function (res) {
            if(res)
            {
                default_wishlist_id = res;
                $(".wishlist_default_dot").each(function(){
                    $(this).css('visibility','hidden')
                })
                $("#wishlist_default_dot_"+name_id).css('visibility','visible');

                $(".Wishlist_default_icon").each(function(){
                    $(this).css('visibility','hidden');
                })
                $("#Wishlist_default_icon_"+name_id).css('visibility','visible');
                 
            }
        });
    }

    function add_product_to_wishlist($el){
        if (!current_product_id){
            current_product_id = $el.attr("product_id");
        }
        var name_id;
        if(selected_wishlist_id){name_id = selected_wishlist_id;}
        else{name_id = default_wishlist_id;}
        if (current_product_id && name_id) {
            ajax.jsonRpc('/wishlist/add_to_wishlist', 'call', {
                'product': current_product_id,"name_id":name_id,
            }).then(function (count) {
                var c_p_id = current_product_id;
                if(count>=0)
                {   
                    product_ids_in_wish.push(current_product_id)
                    if(add_to_wishlist_action=="default"){
                        $('#added_to_default_wishlist_'+c_p_id).fadeIn(500).delay(1000).fadeOut(5);
                        $('#added_to_default_wishlist_'+c_p_id +' span:nth-child(2)').html('Added to');
                    }
                    if(name_id==default_wishlist_id){
                        $('.product_page_status').fadeIn(500).delay(2000).fadeOut(500);                           
                    }
                    $('#wishlist_product_count_'+name_id).html(count+" Product(s)");
                    $('#wishlist_header_product_count_'+name_id).html(count+" Product(s)");
                    $('#tab_menu_product_count_'+name_id).html(count+" Product(s)");
                    // Change Home page heart ICON
                    if($current_heart_element){
                        if($current_heart_element.hasClass('black_heart_icon')){
                            $current_heart_element.removeClass("black_heart_icon").addClass('white_heart_icon').prop('title','Remove from wishlist');
                        }
                    }
                    // Change popover Heart icon
                    if($el){
                        if($el.hasClass('add_product_to_wishlist')){
                            $el.removeClass("add_product_to_wishlist"); $el.addClass('remove_from_wishlist').prop('title','Remove from wishlist');
                            $el.removeClass("black_heart_icon"); $el.addClass('white_heart_icon');   
                        }
                        $('#wishlist_added_status_'+name_id).removeClass('hidden');
                    }
                    // Change Product page button 
                    added_to_wishlist_button();

                    // This code will execute when the product will added while creating wishlist
                    if(!$el){
                        if($($current_heart_element).hasClass('clicked')){
                            $($current_heart_element).removeClass('clicked');
                        }
                        reload_popover_wishlists();
                    }
                }
                else{
                    return false;
                    }
            });
        }       
    }
    function added_to_wishlist_button(){
        if($('.add_to_wishlist_button .blank_heart_icon')){
            $('.add_to_wishlist_button .blank_heart_icon').removeClass('blank_heart_icon').addClass('red_heart_icon');
            $('.add_to_wishlist_button .product_status').html('Added to wishlist');
            $('.add_to_wishlist_button').addClass('added_to_wishlist')
        }
    }
    function add_to_wishlist_button(){
        if($('.add_to_wishlist_button .red_heart_icon')){
            $('.add_to_wishlist_button .red_heart_icon').removeClass('red_heart_icon').addClass('blank_heart_icon')
            $('.add_to_wishlist_button .product_status').html('Add to wishlist')
            $('.add_to_wishlist_button').removeClass('added_to_wishlist')
        }   
    }
    function remove_from_wishlist($el){
        var product_id;
        product_id=$el.attr('product_id')

        // console.log("product_id rem",product_id)
        if(!product_id)
            product_id = current_product_id
        

        var name_id = $el.attr("name_id");if(!name_id){name_id=default_wishlist_id;}
        // console.log("name_id",name_id);
        var $target= $el.closest('tr');
        
        ajax.jsonRpc('/wishlist/remove_from_wishlist', 'call', {
            'product_id': product_id,'name_id':name_id,
        })
        .then(function(count) {
            var c_p_id = current_product_id;
            if(count ||count==0){
                
                product_ids_in_wish.splice(product_ids_in_wish.indexOf(current_product_id),1)
                if(add_to_wishlist_action=="default"){
                    $('#added_to_default_wishlist_'+c_p_id).fadeIn(500).delay(1000).fadeOut(500);
                    $('#added_to_default_wishlist_'+c_p_id +' span:nth-child(2)').html('Removed from');
                }

                $('#wishlist_product_count_'+name_id).html(count+" Product(s)")
                $('#wishlist_header_product_count_'+name_id).html(count+" Product(s)")
                $('#tab_menu_product_count_'+name_id).html(count+" Product(s)")
            
                if(!$el.hasClass('white_heart_icon')){
                    $target.fadeOut("slow");
                }else if($el.hasClass('white_heart_icon')){
                    $el.addClass("black_heart_icon").removeClass('white_heart_icon').prop('title','Add to wishlist');
                }
                if($el.hasClass('remove_from_wishlist')){
                    $el.removeClass("remove_from_wishlist").addClass('add_product_to_wishlist').prop('title','Add to wishlist');  
                    $el.removeClass("white_heart_icon").addClass('black_heart_icon');
                }     
                $('#wishlist_added_status_'+name_id).addClass('hidden');
                
                if($('.remove_from_wishlist').length==0){
                    if($current_heart_element){
                        if($current_heart_element.hasClass('white_heart_icon')){
                            $current_heart_element.addClass("black_heart_icon").removeClass('white_heart_icon').prop('title','Add to wishlist');
                        }
                    }
                    add_to_wishlist_button(); 
                }
                if(last_product)
                    window.location.reload();
            
            }else{
                console.log("wishlist product  NOT Removed");
            }  
        });      
    }
    function move_to_wishlist(product_id,source_id,target_id){
        if(source_id==target_id){
            return false;
        }
        ajax.jsonRpc("/shop/wishlist/product/move",'call',{
            'product_id':product_id,
            'source_id':source_id,
            'target_id':target_id})
            .then(function(res){
                if(res){
                    reload_tab_view();
                }
                else{
                    $('#wishlist_notify_warning').html(  "Warning! product is already present there ").fadeIn().delay(2000).fadeOut();
                }
            });
    }
    function reload_tab_view(){
        $.get('/shop/wishlist/tabview/',{})
            .then(function(data){
                $('#wishlist_tab_view_container').html(data);
                    $("#wishlist_tab_view_container").html(data);
                    $(".wishlist_tap ").removeClass("wishlist_tap_selected");
                    $("#wishlist_tab_link_"+selected_wishlist_id).addClass("wishlist_tap_selected");
                    $(".wishlist_tab_content").addClass("hidden");
                    $("#wishlist_tab_content_"+selected_wishlist_id).removeClass("hidden");  
            });    
    }
    function check_product_id() {
        if ($("input[name='product_id']").is(':radio'))
            var product_id = $("input[name='product_id']:checked").attr('value');
        else
            var product_id = $("input[name='product_id']").attr('value');
        if (product_id === '0') {
            $("div.wishlist-box").hide();
        } else {
            $("div.wishlist-box").show();
        }
        return product_id
    }
   
    function get_default_wishlist_id(){
    // This function will return Delfault selected wishlist
        ajax.jsonRpc('/shop/default/wishlist/', 'call', {
        }).then(function (data) {
            default_wishlist_id=data.name_id;
            add_to_wishlist_action = data.add_to_wishlist_action;
        });
    }
    

});




















