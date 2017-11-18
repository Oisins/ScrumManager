var users = {};
var unsaved_changes = false;
var editing_task = {};
var editing_story = {};
var task_id = 0;
var modal;
var taskboard;

var task_template = `
        <div class="border border-dark rounded p-3 m-2 bg-white task">
            <button class="float-right btn btn-link edit-task" type="button">
                <i class="fa fa-pencil" aria-hidden="true"></i>
            </button>
            <span class="task-name"><!-- Name --></span>
            <i class="d-block text-muted task-user"><!-- Nutzer --></i>
        </div>`;

var story_template = `
        <tr>
            <td>
                <button class="float-right btn btn-light edit-story" type="button">
                    <i class="fa fa-pencil" aria-hidden="true"></i>
                </button>
                <h5 class="story-name"><!-- Name --></h5>
                <span class="story-beschreibung"><!-- Beschreibung --></span>
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

        // DOM Objekt erstellen
        this.dom = $(task_template);
        this.dom.draggable();

        // Events
        this.dom.find(".edit-task").click(this.edit.bind(this)); // .bind() da this sonst event object ist
        this.dom.bind("task_drop", (event, parent) => this.drop(parent));
        this.story.dom.find(`td[data-status="${this.status}"]`).append(this.dom);
    }

    drop(parent) {
        this.move_dom(parent);

        var cell = this.dom.parent();
        this.status = cell.data("status");
        var new_story = Story.get(cell.parent().data("story"));

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
        unsaved_changes = true;

        this.name = $("#task-name").val();

        var user = users[$("#task-user").val()];
        if (user) {
            this.user = user;
        }

        taskboard.update_data();
    }

    remove() {
        unsaved_changes = true;

        this.story.remove_task(this);

        this.dom.remove();

        taskboard.update_data();
    }

    move_dom(new_parent) {
        this.dom.detach().appendTo(new_parent);
    }

    update_dom() {
        var name = this.name ? this.name : "[Kein Name]";
        this.dom.find(".task-name").html(name);

        var user = this.user.name !== -1 ? this.user.name : "Nicht zugewiesen";
        this.dom.find(".task-user").html(user);
    }

    to_json() {
        return {
            "id": this.id,
            "name": this.name,
            "status": this.status,
            "story_id": this.story.id,
            "user_id": this.user.id
        }
    }
}

class Story {
    constructor(id, name = "", beschreibung = "", tasks = []) {
        this.id = id || uuid();
        this.to_delete = false;
        this.name = name;
        this.beschreibung = beschreibung;
        this.tasks = tasks;

        // DOM Objekt erstellen und ID einfügen
        this.dom = $(story_template);
        this.dom.attr("data-story", this.id); // .data() fügt daten nichts ins DOM
        var body = taskboard.dom.find("tbody");
        body.last().before(this.dom); // Zum Taskboard hinzufügen

        this.dom.find(".edit-story").click(() => this.edit());

        this.dom.find("td[data-status]").droppable({
            drop: function (event, ui) {
                unsaved_changes = true;

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
        return taskboard.stories.find(story => story.id === id);
    }

    add_task(task) {
        task.story = this;
        this.tasks.push(task);
    }

    remove_task(task) {
        task.story = null;
        this.tasks = this.tasks.filter(tsk => tsk !== task);
    }

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
        unsaved_changes = true;

        this.beschreibung = $("#story-beschreibung").val();

        taskboard.update_data();
    }

    remove() {
        unsaved_changes = true;
        this.to_delete = true;

        for (var task of this.tasks) {
            task.remove();
        }
        this.dom.remove();

        taskboard.update_data();
    }

    to_json() {
        return {
            "id": this.id,
            "to_delete": this.to_delete,
            "beschreibung": this.beschreibung,
            "tasks": this.tasks.map(task => task.to_json())
        }
    }
}

class TaskBoard {
    constructor(sprint_id) {
        this.stories = [];
        this.sprint_id = sprint_id

    }

    ready() {
        this.dom = $("#taskboard");

        // Anfragen parallel ausführen
        $.when(
            // Liste von Tasks anfragen und Tasks erstellen
            $.getJSON("/api/sprint/" + this.sprint_id).done(data => {
                var story;

                /** @namespace data.stories */
                for (var s of data.stories) {
                    story = new Story(s.id, s.name, s.beschreibung, s.tasks);
                    this.stories.push(story);

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
        ).done(() => {
            this.update_data();
            this.bind_listeners();
            modal.modal("hide");
        });
    }

    update_data() {
        for (var story of this.stories) {
            if (story.to_delete) {
                continue;
            }
            story.update_dom();

            for (var task of story.tasks) {
                task.update_dom();
            }
        }
    }

    bind_listeners() {
        /**
         * Task
         *  - Erstellen
         *  - Speichern
         *  - Löschen
         */
        $("#task-create").click(() => {
            if (this.stories.length === 0) {
                // Error
                return;
            }
            var task = new Task("", 0, users[0], this.stories[0]);
            this.stories[0].tasks.push(task);
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
         * Speichern
         * Daten zusammenfügen und an Server schicken
         */
        $("#speichern").click(() => {
            // Warnung ausschalten
            unsaved_changes = false;

            var data = this.stories.map(story => story.to_json());

            // Daten in hidden input einfügen
            $("#data-input").val(JSON.stringify(data));

            // Form abschicken
            $(this).parent().submit();
        });
    }
}

function uuid() {
    /**
     * UUID Generator
     */
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c === "x" ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function init(sprint_id) {
    taskboard = new TaskBoard(sprint_id);
    $(function () {
        taskboard.ready();
    });
}

$(function () {
    // "Laden..." anzeigen
    modal = $("#loadingModal").modal();

    // Datumsauswahl Plugin aktivieren, da FF keine native support hat
    $("input.date-input").datepicker({dateFormat: "dd.mm.yy"});

    // Warnung für nicht gespeicherte Daten
    $(window).bind("beforeunload", function () {
        if (unsaved_changes) return true; // Ja, muss so sein
    });
});

