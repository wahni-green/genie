// Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and Contributors
// MIT License. See license.txt
// Recording part referrenced from https://github.com/TylerPottsDev/yt-js-screen-recorder

frappe.provide("genie");

genie.chunks = [];
genie.blob = null;
genie.blobURL = null;

genie.SupportTicket = class SupportTicket {
	constructor() {
		this.init_config();
		this.setup_dialog();
		this.dialog.show();
	}

	setup_dialog() {
		this.dialog = new frappe.ui.Dialog({
			title: __("Support Ticket"),
			size: "large",
			minimizable: true,
			static: true,
			fields: [
				{
					fieldname: "ticket_title",
					label: __("Title"),
					fieldtype: "Data",
					reqd: 1
				},
				{
					fieldname: "ticket_description",
					label: __("Description"),
					fieldtype: "Text Editor",
					reqd: 1
				},
				{
					fieldtype: "Section Break",
					label: __("Screen Recording")
				},
				{
					fieldname: "record_screen",
					label: __("Start Recording"),
					fieldtype: "Button",
					click: () => {
						if (this.recorder && this.recorder.state == "recording") {
							this.recorder.stop();
							this.dialog.set_df_property("record_screen", "label", "Start Recording")
							this.dialog.set_df_property("view_recording", "hidden", 0);
							frappe.show_alert({
								indicator: "green",
								message: __(`Screen recording has stopped. Please click on "View Recording" to view the recording.`)
							})
						} else {
							this.startRecording();
							this.dialog.set_df_property("record_screen", "label", "Stop Recording");
							this.dialog.set_df_property("view_recording", "hidden", 1);
							frappe.show_alert({
								indicator: "green",
								message: __(`Screen recording has started. Please click on "Stop Recording" once you are done.`)
							})
						}
					}
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "view_recording",
					label: __("View Recording"),
					fieldtype: "Button",
					hidden: 1,
					click: () => {
						window.open(genie.blobURL, "_blank");
					}
				}
			],
			primary_action_label: __("Raise Ticket"),
			primary_action: (values) => {
				this.raise_ticket(values);
			},
			secondary_action_label: __("Cancel"),
			secondary_action: () => {
				this.dialog.hide();
			}
		});
	}

	async raise_ticket(values) {
		let screen_recording = null;
		if (genie.blob) {
			screen_recording = await this.blobToBase64(genie.blob);
		}

		frappe.call({
			method: "genie.utils.support.create_ticket",
			type: "POST",
			args: {
				"title": values.ticket_title,
				"description": values.ticket_description,
				"screen_recording": screen_recording
			},
			freeze: true,
			freeze_message: __("Creating ticket..."),
			callback: (r) => {
				if (!r.exc && r.message) {
					frappe.show_alert({
						indicator: "green",
						message: __("Ticket raised successfully"),
					})
					this.dialog.hide();
					frappe.msgprint(
						__(`Your ticket(#${r.message}) has been raised successfully. You will be notified once it is resolved.`)
					)
				}
			}
		});
	}

	init_config() {
		this.stream = null;
		this.audio = null;
		this.mixedStream = null;
		this.recorder = null;
		this.recordedVideo = null;

		genie.chunks = [];
		genie.blob = null;
		genie.blobURL = null;
	}

	async setupStream() {
		try {
			this.stream = await navigator.mediaDevices.getDisplayMedia({
				video: true
			});

			this.audio = await navigator.mediaDevices.getUserMedia({
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					sampleRate: 44100,
				},
			});
		} catch (err) {
			console.error(err)
		}
	}

	async startRecording() {
		await this.setupStream();

		if (this.stream && this.audio) {
			genie.chunks = [];
			this.mixedStream = new MediaStream([...this.stream.getTracks(), ...this.audio.getTracks()]);
			this.recorder = new MediaRecorder(this.mixedStream);
			this.recorder.ondataavailable = (e) => {
				genie.chunks.push(e.data);
			};
			this.recorder.onstop = this.handleStop;
			this.recorder.start(1000);
			console.log('Recording started');
		} else {
			console.warn('No stream available.');
		}
	}

	handleStop(e) {
		genie.blob = new Blob(genie.chunks, { 'type': 'video/mp4' });
		genie.blobURL = URL.createObjectURL(genie.blob);

		this.stream.getTracks().forEach((track) => track.stop());
		this.audio && this.audio.getTracks().forEach((track) => track.stop());

		console.log('Recording stopped');
	}

	blobToBase64(blob) {
		// Taken from https://stackoverflow.com/a/18650249
		return new Promise((resolve, _) => {
			let reader = new FileReader();
			reader.onloadend = function () {
				let dataUrl = reader.result;
				let base64 = dataUrl.split(',')[1];
				resolve(base64)
			};
			reader.readAsDataURL(blob);
		});
	}
}
