//var tasks = [];
var users = {};
var stories = [];
var confirm = false;
var editing_task = {};
var editing_story = {};
var task_id = 0;
var story_id = 0;
var modal;
var taskboard;

var task_template = `
        <div class="border border-dark rounded p-3 m-2 bg-white task">
            <button class="float-right btn btn-link edit-task" type="button">
                <i class="fa fa-pencil" aria-hidden="true"></i>
            </button>
            <span class="task-name"></span>
            <i class="d-block text-muted task-user"></i>
        </div>`;

var story_template = `
        <tr>
            <td>
                <button class="float-right btn btn-light edit-story" type="button">
                    <i class="fa fa-pencil" aria-hidden="true"></i>
                </button>
                <h5 class="story-name"></h5>
                <span class="story-beschreibung"></span>
            </td>
            <td class="task-cell" data-status="0"></td>
            <td class="task-cell" data-status="1"></td>
            <td class="task-cell" data-status="2"></td>
        </tr>`;

class Task {
    constructor(name = "", status = 0, user = {id: -1}, story = {}) {
        this.id = task_id++; // ID für nutzung in diesem Script
        this.status = status;
        this.story = story;
        this.name = name;
        this.user = user;

        // DOM Objekt erstellen und ID einfügen
        this.dom = $(task_template);
        this.dom.draggable();

        // Events
        this.dom.find(".edit-task").click(() => this.edit()); // Hack, da sonst "this" sich auf das Element bezieht
        this.dom.bind("task_drop", (event, parent) => this.drop(parent));
        this.story.dom.find(`td[data-status="${this.status}"]`).append(this.dom);
    }

    drop(parent) {
        this.move_dom(parent);


        var cell = this.dom.parent();
        this.status = cell.data("status");
        var new_story = Story.get(cell.parent().data("story"));

        /**/

        this.story.remove_task(this);
        new_story.add_task(this);
    }

    edit() {
        editing_task = this;

        $("#task-name").val(this.name);
        $("#task-user").val(this.user.id);

        $("#editTaskModal").modal({backdrop: 'static', keyboard: false});
    }

    save() {
        confirm = true;

        this.name = $("#task-name").val();

        var user = users[$("#task-user").val()];
        if (user) {
            this.user = user;
        }

        update_data();
    }

    remove() {
        confirm = true;

        this.dom.remove();

        update_data();
    }

    move_dom(new_parent) {
        this.dom.detach().appendTo(new_parent);
    }

    update_dom() {
        this.dom.find(".task-name").html(this.name);
        this.dom.find(".task-user").html(this.user.name);
    }

    to_json() {
        return {
            "id": this.db_id,
            "name": this.name,
            "status": this.status,
            "story_id": this.story.id,
            "user_id": this.user.id
        }
    }
}

class Story {
    constructor(db_id = -1, name = "", beschreibung = "", tasks = []) {
        stories.push(this);

        this.id = story_id++; // ID für nutzung in diesem Script
        this.db_id = db_id; // ID für Speicherung in Datenbank
        this.name = name;
        this.beschreibung = beschreibung;
        this.tasks = tasks;

        // DOM Objekt erstellen und ID einfügen
        this.dom = $(story_template);
        this.dom.attr("data-story", this.id); // .data() fügt daten nichts ins DOM
        var body = taskboard.find("tbody");
        body.last().before(this.dom); // Zum Taskboard hinzufügen

        this.dom.find(".edit-story").click(() => this.edit());

        this.dom.find("td[data-status]").droppable({
            drop: function (event, ui) {
                confirm = true;

                ui.draggable.trigger("task_drop", [$(this)]);
            },
            deactivate: function (event, ui) {
                var drag = ui.draggable;

                drag.css("left", "");
                drag.css("top", "");
            }
        });
    }

    static get(id) {
        return stories.find(story => story.id === id);
    }

    add_task(task) {
        task.story = this;
        this.tasks.push(task);
    }

    remove_task(task) {
        task.story = null;
        this.tasks = this.tasks.filter(tsk => tsk !== task);
    }

    /*move_dom(new_parent) {
        this.dom.detach().insertBefore(new_parent.find("tbody").children().last());
    }*/

    update_dom() {
        this.dom.find(".story-name").html("");
        this.dom.find(".story-beschreibung").html(this.beschreibung);
    }

    edit() {
        editing_story = this;

        $("#story-beschreibung").val(this.beschreibung);

        $("#editStoryModal").modal({backdrop: 'static', keyboard: false});
    }

    save() {
        confirm = true;

        this.beschreibung = $("#story-beschreibung").val();

        update_data();
    }

    remove() {
        confirm = true;

        for (var task of this.tasks) {
            task.remove();
        }

        this.dom.remove();
        stories = stories.filter(story => story !== this);

        update_data();
    }

    to_json() {
        return {
            "id": this.db_id,
            "beschreibung": this.beschreibung,
            "tasks": this.tasks.map(task => task.to_json())
        }
    }
}

$(function () {
    // "Laden..." anzeigen
    modal = $("#loadingModal").modal();

    // Datumsauswahl Plugin aktivieren, da FF keine native support hat
    $("input.date-input").datepicker({dateFormat: "dd.mm.yy"});

    // Warnung für nicht gespeicherte Daten
    $(window).bind("beforeunload", function () {
        if (confirm) return true; // Ja, muss so sein
    });

    taskboard = $("#taskboard");
});

function get_data(sprint_id) {
    // Anfragen parallel ausführen
    $.when(
        // Liste von Tasks anfragen
        $.getJSON("/api/sprint/" + sprint_id).done(function (data) {
            // Tasks erstellen

            var story;
            /** @namespace data.stories */
            for (var s of data.stories) {
                story = new Story(s.id, s.name, s.beschreibung, s.tasks);

                story.tasks = story.tasks.map(task => {
                    return new Task(task.name, task.status, task.user, story);
                });
            }
        }),
        // Liste von Users anfragen
        $.getJSON("/api/users").done(function (data) {
            for (var user of data) {
                users[user.id] = user;
            }
        })
    ).done(function () {
        update_data();

        modal.modal("hide");
        ready();
    });
}


// Taskboard aktualisieren
function update_data() {
    for (var story of stories) {
        story.update_dom();

        for (var task of story.tasks) {
            task.update_dom();
        }
    }
}


function ready() {
    /**
     * Task
     *  - Erstellen
     *  - Speichern
     *  - Löschen
     */
    $("#task-create").click(() => {
        if (stories.length === 0) {
            // Error
            return;
        }
        var task = new Task("", 0, users[0], stories[0]);
        stories[0].tasks.push(task);
        task.edit();
    });
    $("#task-save").click(() => editing_task.save());
    $("#task-delete").click(() => editing_task.remove());

    /**
     * Story
     *  - Erstellen
     *  - Speichern
     *  - Löschen
     */
    $("#story-create").click(() => {
        var story = new Story();
        story.edit();
    });
    $("#story-save").click(() => editing_story.save());
    $("#story-delete").click(() => editing_story.remove());


    /**
     * Daten zusammenfügen und an Server schicken
     */
    $("#speichern").click(function () {
        // Warnung ausschalten
        confirm = false;

        var data = stories.map(story => story.to_json());

        // Daten in hidden input einfügen
        $("#data-input").val(JSON.stringify(data));

        // Form abschicken
        $(this).parent().submit();
    });
}