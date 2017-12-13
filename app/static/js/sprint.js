var users = {};
var editing_task = {};
var editing_story = {};
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
                <h6 class="mt-3">Kriterien:</h6>
                <ul class="story-kriterien"></ul>
            </td>
            <td class="task-cell" data-status="0"></td>
            <td class="task-cell" data-status="1"></td>
            <td class="task-cell" data-status="2"></td>
        </tr>`;

class Task {
    constructor(id = -1, name = "", status = 0, user = {id: -1}, story = {}) {
        this.id = id;
        this.status = status;
        this.story = story;
        this.name = name;
        this.user = user;
        this.delete = false;

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

        if (new_story !== this.story) {
            taskboard.unsaved_changes = true;
            this.story.remove_task(this);
            new_story.add_task(this);
        }
    }

    edit() {
        editing_task = this;

        $("#taskNameInput").val(this.name);
        $("#taskUserSelect").val(this.user.id);

        $("#editTaskModal").modal({backdrop: 'static', keyboard: false});
    }

    save() {
        taskboard.unsaved_changes = true;

        this.name = $("#taskNameInput").val();
        var user_id = $("#taskUserSelect").val();

        if (user_id === "-1") {
            this.user = {id: -1}
        } else {
            var user = users[user_id];
            if (user) {
                this.user = user;
            }
        }

        this.update_dom();
    }

    remove() {
        taskboard.unsaved_changes = true;

        this.delete = true;

        this.dom.remove();
        taskboard.update_data();
    }

    move_dom(new_parent) {
        this.dom.detach().appendTo(new_parent);
    }

    update_dom() {
        var name = this.name ? this.name : "[Kein Name]";
        this.dom.find(".task-name").html(name);

        var user = this.user.id === -1 ? "Nicht zugewiesen" : this.user.name;
        this.dom.find(".task-user").html(user);
    }

    to_json() {
        return {
            "id": this.id,
            "name": this.name,
            "status": this.status,
            "story_id": this.story.id,
            "user_id": this.user.id,
            "delete": this.delete
        }
    }
}

class Story {
    constructor(id, name = "", beschreibung = "", tasks = [], kriterien = []) {
        this.id = id || uuid();
        this.to_delete = false;
        this.titel = name;
        this.beschreibung = beschreibung;
        this.tasks = tasks;
        this.kriterien = kriterien;

        // DOM Objekt erstellen und ID einfügen
        this.dom = $(story_template);
        this.dom.attr("data-story", this.id); // .data() fügt daten nichts ins DOM
        var body = taskboard.dom.find("tbody");
        body.last().before(this.dom); // Zum Taskboard hinzufügen

        this.dom.find(".edit-story").click(() => this.edit());

        this.dom.find("td[data-status]").droppable({
            drop: function (event, ui) {
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
        this.dom.find(".story-name").html(this.titel);
        this.dom.find(".story-beschreibung").html(this.beschreibung);

        var kriterien_div = this.dom.find(".story-kriterien");
        kriterien_div.html("");
        this.kriterien.map(kriterium => {
            kriterien_div.append(`<li>${kriterium.beschreibung}</li>`);
        });
    }

    edit() {
        editing_story = this;

        $("#storyTitleInput").val(this.titel);
        $("#storyBeschreibungTextarea").val(this.beschreibung);

        $("#editStoryModal").modal({backdrop: 'static', keyboard: false});
    }

    save() {
        taskboard.unsaved_changes = true;

        this.titel = $("#storyTitleInput").val();
        this.beschreibung = $("#storyBeschreibungTextarea").val();

        taskboard.update_data();
    }

    remove() {
        taskboard.unsaved_changes = true;
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
            "titel": this.titel,
            "beschreibung": this.beschreibung,
            "tasks": this.tasks.map(task => task.to_json())
        }
    }
}

class TaskBoard {
    constructor(sprint_id) {
        this.stories = [];
        this.sprint_id = sprint_id;
        this._unsaved_changes = false;

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
                    story = new Story(s.id, s.titel, s.beschreibung, s.tasks, s.kriterien);
                    this.stories.push(story);

                    story.tasks = story.tasks.map(task => {
                        return new Task(task.id, task.name, task.status, task.user, story);
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

    set unsaved_changes(val) {
        this._unsaved_changes = val;
        if (val) {
            var speichern = $("#speichern");
            speichern.removeClass("btn-outline-success");
            speichern.addClass("btn-warning");
        }
    }

    get unsaved_changes() {
        return this._unsaved_changes;
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
            var task = new Task(-1, "", 0, users[0], this.stories[0]);
            this.stories[0].tasks.push(task);
            task.edit();
        });
        $("#editTaskModalSave").click(() => editing_task.save());
        $("#editTaskModalDelete").click(() => editing_task.remove());

        /**
         * Story
         *  - Erstellen
         *  - Speichern
         *  - Löschen
         */
        $("#story-create").click(() => {
            var story = new Story();
            story.edit();
            this.stories.push(story);
        });
        $("#editStoryModalSave").click(() => editing_story.save());
        $("#editStoryModalDelete").click(() => editing_story.remove());


        /**
         * Speichern
         * Daten zusammenfügen und an Server schicken
         */
        $("#speichern").click(() => {
            // Warnung ausschalten
            this.unsaved_changes = false;

            var data = this.stories.map(story => story.to_json());

            // Daten in hidden input einfügen
            $("#data-input").val(JSON.stringify(data));

            // Form abschicken
            $(this).parent().submit();
        });

        $("#sprint-form").find("input,textarea").on('change input propertychange paste', () => {
            taskboard.unsaved_changes = true;
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
        if (taskboard.unsaved_changes) return true; // Ja, muss so sein
    });
});

