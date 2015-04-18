/*
Eventually, this page should be able to do the following things:
(1) find the relevant participants for a given event and 
(2) display information about each of them, then 
(3) offer textboxes populated by values from that object onclick of an edit button
(4) save changes made via those text boxes
(5) remove a relationship between a person and an event, 
(6) add an entirely new person (really the same as (4)), 
(7) search for and 
(8) link an existing person to this event.

Currently it does only number two (2), of the above.
*/



function makePersonEditable(person_id){
    
}

function makePersonDisplayOnly(person_id){
    
}

function savePerson(person_object, event_id){
    //send info about an existing person to Jess's save endpoint
    var target_url = '/api/participants/'+person_object.id+'/';
    var person_parsed = JSON.stringify(person_object, null, 2);
    $.ajax({
        url: target_url,
        type: 'PUT',
        dataType: 'json',
        data: person_object,
        contentType: "application/json; charset=UTF-8",
        error: function(XMLHttpRequest, textStatus, errorThrown, result){
            alert(errorThrown);
        }, 
        success: function(result){
        }
    });
}


function getAvailableParticipants(){
    var event_id = document.getElementById('event_object_id').value;
    var url = '/api/events/'+event_id+'/available-participants';
    $.get(url,  function (result){
        var $select_available = $('<select>');
        for (i = 0; i < result.length; i++){
            $select_available.append('<option value="'+result[i].id+'">'+result[i].first_name+' '+result[i].last_name);
        }
        $('.module').append($select_available);
    });
}



function unlinkPerson(event_id, person_id){
    //send info about this person to Jess's delete endpoint
    var target_url = '/api/events/'+event_id+'/participants/'+person_id+'/';
    $.ajax({
        url: target_url,
        type: 'DELETE',
        success: function(result) {
            location.reload();
        }
    });
}

function linkPerson(event_id, person_id){
    var target_url = '/api/events/'+event_id+'/participants/'+person_id+'/';
    $.ajax({
        url: target_url,
        type: 'POST',
        success: function(result) {
            location.reload();
        }
    });
}

/*
Loops through attendees and creates table rows to display and edit them
*/
function displayPerson(person, event){
    $('.editable').hide();
//    $('#attendees_table').append('<tr></tr>');
    var $tr = $('<tr>');
    $tr.append('<input class="attendee-id" type="hidden" value="'+person.id+'" />');
    var person_info = [person.first_name, person.last_name,
                       person.institution.name, person.phone_number,
                       person.address.number, person.address.direction,
                       person.address.name, person.address.type]; 
    $tr.append('<td>'+person.first_name+'<input type=text class="editable" value="'+person.first_name+'"></td>'); 
    $tr.append('<td>'+person.last_name+'<input type=text class="editable" value="'+person.last_name+'"></td>'); 
    $tr.append('<td>'+person.institution.name+'<input type=text class="editable" value="'+person.institution.name+'"></td>'); 

    $tr.append('<td>'+person.phone_number+'<input type=text class="editable" value="'+person.phone_number+'"></td>'); 

    var $address_td = $('<td>');
    $address_td.append(person.address.number+' '+person.address.direction+' '+person.address.name+' '+person.address.type);
    $address_td.append('<input type=text class="editable" size="5px"  value="'+person.address.number+'">');
    $address_td.append('<input type=text class="editable" size="3px" value="'+person.address.direction+'">');
    $address_td.append('<input type=text class="editable" size="15px" value="'+person.address.name+'">');
    $address_td.append('<input type=text class="editable" size="3px" value="'+person.address.type+'"></td>'); 
    $tr.append($address_td);
    var $btn_cell = $('<td>');
    $edit_btn = $('<input class="btn btn-info display_only" name="_edit" value="Edit" onclick="makePersonEditable('+person.id+')">');
    $btn_cell.append($edit_btn);
    var $save_btn = $('<input class="btn btn-success editable" name="_save" value="✓ Save">');
    $btn_cell.append($save_btn);
    $btn_cell.append('<input class="btn btn-warning editable" name="_cancel" value="✗ Cancel" onclick="makePersonDisplayOnly('+person.id+')">');
    $btn_cell.append('<input class="btn btn-danger display_only" name="_unlink" value="Remove attendee" onclick="unlinkPerson('+event+', '+person.id+')">');

    $tr.append($btn_cell);
    $('#attendees_table').append($tr);
    $('.editable').hide();
}


function getAttendees(){
    var event_id = document.getElementById('event_object_id').value;
    var url = '/api/events/'+event_id+'/participants';
    $.get(url,  function (people_list){
    for (i = 0; i < people_list.length; i++){
        displayPerson(people_list[i], event_id);
    }
    });
}

getAttendees(); 
getAvailableParticipants();