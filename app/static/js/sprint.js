var tasks = [];
var users = {};
var stories = [];
var confirm = false;
var editing_task = {};
var task_id = 0;
var story_id = 0;

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
    constructor(db_id = -1, name = "", status = 0, user = {}, story_id = 1) {
        tasks.push(this);

        this.id = task_id++; // ID für nutzung in diesem Script
        this.db_id = db_id; // ID für Speicherung in Datenbank
        this.status = status;
        this.story_id = story_id;
        this.name = name;
        this.user = user;

        // DOM Objekt erstellen und ID einfügen
        this.dom = $(task_template);
        this.dom.draggable();

        // Events
        this.dom.find(".edit-task").click(() => this.edit()); // Hack, da sonst "this" sich auf das Element bezieht
        this.dom.bind("task_drop", (event, parent) => this.drop(parent));
    }

    drop(parent) {
        this.move_dom(parent);

        var cell = this.dom.parent();
        this.status = cell.data("status");
        this.story_id = cell.parent().data("story");
    }

    edit() {
        editing_task = this;

        $("#task-name").val(this.name);
        $("#task-user").val(this.user.id);

        $("#editTaskModal").modal();
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
        tasks = tasks.filter(task => task.id !== this.id);

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
            "story_id": this.story_id,
            "user_id": this.user.id
        }
    }
}

class Story {
    constructor(db_id = -1, name = "", bescheibung = "") {
        stories.push(this);

        this.id = stories.indexOf(this); // ID für nutzung in diesem Script
        this.db_id = db_id; // ID für Speicherung in Datenbank
        this.name = name; // TODO Remove?
        this.bescheibung = bescheibung;

        // DOM Objekt erstellen und ID einfügen
        this.dom = $(story_template);
        this.dom.attr("data-story", this.db_id); // .data() fügt daten nichts ins DOM
    }

    move_dom(new_parent) {
        this.dom.detach().insertBefore(new_parent.find("tbody").children().last());
    }

    update_dom() {
        this.dom.find(".story-name").html("");
        this.dom.find(".story-beschreibung").html(this.bescheibung);
    }

    to_json() {
        return {
            "id": this.db_id,
            "name": this.name,
            "bescheibung": this.bescheibung
        }
    }
}

$(function () {
    // "Laden..." anzeigen
    var modal = $("#loadingModal").modal();

    // Datumsauswahl Plugin aktivieren, da nicht von FF unterstützt
    $("input.date-input").datepicker({dateFormat: "dd.mm.yy"});

    // Warnung für nicht gespeicherte Daten
    $(window).bind("beforeunload", function () {
        if (confirm) return true; // Ja, muss so sein
    });

    // Anfragen parallel ausführen
    $.when(
        // Liste von Tasks anfragen
        $.getJSON("/api/tasks").done(function (data) {
            // Tasks erstellen
            for (var task of data) {
                new Task(task.id, task.name, task.status, task.user, task.story_id);
            }
        }),
        // Liste von Users anfragen
        $.getJSON("/api/users").done(function (data) {
            for (var user of data) {
                users[user.id] = user;
            }
        }),
        // Liste von Stories anfragen
        $.getJSON("/api/stories").done(function (data) {
            for (var story of data) {
                new Story(story.id, story.name, story.beschreibung);
            }
        })
    ).done(function () {
        update_data();

        modal.modal("hide");
        ready();
    });
});

// Taskboard aktualisieren
function update_data() {
    var taskboard = $("#taskboard");

    for (var story of stories) {
        story.move_dom(taskboard);
        story.update_dom();
    }

    for (var task of tasks) {
        // Passende Zelle finden nach status und story
        var parent = taskboard.find(`tr[data-story="${task.story_id}"]`).find(`td[data-status="${task.status}"]`);

        task.move_dom(parent);
        task.update_dom();
    }
}


function ready() {
    var taskboard = $("#taskboard");

    // Nur auf Zellen mit Daten (nur die wo es hin soll haben diese attr.) verschieben lassen
    taskboard.find("[data-story]").find("td[data-status]").droppable({
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

    /**
     * Task Bearbeiten
     */
    $("#task-create").click(() => {
        var task = new Task();
        task.edit();
    });

    /**
     * Task Speichern
     */
    $("#task-save").click(() => editing_task.save());

    /**
     * Task löschen
     */
    $("#task-delete").click(() => editing_task.remove());

    /**
     * Daten zusammenfügen und an Server schicken
     */
    $("#speichern").click(function () {
        // Warnung ausschalten
        confirm = false;

        var data = {
            "tasks": tasks.map(task => task.to_json()),
            "stories": stories.map(story => story.to_json())
        };

        // Daten in hidden input einfügen
        $("#data-input").val(JSON.stringify(data));

        // Form abschicken
        $(this).parent().submit();
    });
}