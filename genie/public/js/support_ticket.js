// Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and Contributors
// MIT License. See license.txt
// Recording part referrenced from https://github.com/TylerPottsDev/yt-js-screen-recorder

frappe.provide("genie");

genie.chunks = [];
genie.blob = null;
genie.blobURL = null;

genie.SupportTicket = class SupportTicket {
	constructor() {
		if (!frappe.boot.genie_support_enabled) {
			frappe.msgprint(__("Ticket raising is not enabled for this site."));
			return;
		}
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
					fieldtype: "Section Break",
					label: __("User Details")
				},
				{
					fieldname: "ticket_email",
					label: __("Email"),
					fieldtype: "Read Only",
					reqd: 1,
					default: frappe.session.user_email,
					
				},
				{
					fieldtype: "Column Break"
				},
				{
					fieldname: "ticket_user",
					label: __("User"),
					fieldtype: "Read Only",
					reqd: 1,
					default: frappe.session.user_fullname,
					
				},
				{
					fieldtype: "Column Break"
				},
				{
					fieldname: "ticket_whatsapp",
					label: __("Whatsapp Number"),
					fieldtype: "Data",
					description:"(Country code is mandatory.)"
					
				},
				{
					fieldtype: "Section Break",
					label: __("Description")
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
					label: 'Hidden Field',
					fieldtype: 'Data',
					hidden: 1,
					read_only: 1
				},
				{
					fieldtype: "Column Break"
				},
				{
					fieldname: "record_screen",
					label: __("Start Recording"),
					fieldtype: "Button",
					description:"Prefer to speak? Raise your issue using voice while recording.",
					click: () => {
						if (this.recorder && this.recorder.state == "recording") {
							this.stopRecording();
						} else {
							this.startRecording();
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
				},
				{
					fieldname: "clear_recording",
					label: __("Clear Recording"),
					fieldtype: "Button",
					hidden: 1,
					click: () => {
						if (this.recorder && this.recorder.state == "recording") {
							frappe.show_alert({
								indicator: "red",
								message: __("Please stop the recording before clearing.")
							});
							return;
						}

						genie.chunks = [];
						genie.blob = null;
						genie.blobURL = null;

						this.dialog.set_df_property("record_screen", "label", "Start Recording")
						this.dialog.set_df_property("view_recording", "hidden", 1);
						this.dialog.set_df_property("clear_recording", "hidden", 1);

						frappe.show_alert({
							indicator: "green",
							message: __("Screen recording have been cleared.")
						});
					}
				}
			],
			primary_action_label: __("Raise Ticket"),
			primary_action: (values) => {
				if (this.recorder && this.recorder.state == "recording") {
					frappe.show_alert({
						indicator: "red",
						message: __("Please stop the recording before raising the ticket.")
					});
					return;
				}
				this.raise_ticket(values);
			},
			secondary_action_label: __("Cancel"),
			secondary_action: () => {
				if (this.recorder && this.recorder.state == "recording") {
					frappe.show_alert({
						indicator: "red",
						message: __("Please stop the recording before cancelling.")
					});
					return;
				}
				this.dialog.hide();
			}
		});

		this.dialog.$wrapper.find(".modal-dialog").css("z-index", 1);
		this.dialog.get_minimize_btn().addClass("pr-3");
	}

	setIndicator(indicator) {
		this.dialog.header
			.find(".indicator")
			.css({ width: "1rem", height: '1rem'})
			.removeClass()
			.addClass("indicator " + (indicator || "hidden"));
	}

	async raise_ticket(values) {
		console.log(this.inUpload)
		if (this.inUpload) return;

		this.inUpload = true;
		let screen_recording = null;
		if (genie.blob) {
			frappe.show_alert({
				indicator: "yellow",
				message: __("Raising ticket. Please wait..."),
			})
			screen_recording = await this.blobToBase64(genie.blob);
			screen_recording = await genie.UploadFile(genie.blob);
			if (!screen_recording) {
				frappe.show_alert({
					indicator: "red",
					message: __("Error raising ticket. Please try again."),
				})
				this.inUpload = false;
				return;
			}
		}

		this.inUpload = false;
		frappe.call({
			method: "genie.utils.support.create_ticket",
			type: "POST",
			args: {
				"title": values.ticket_title,
				"status":"Open",
				"email": values.ticket_email,
				"user":values.ticket_user,
				"whatsapp_no":values.ticket_whatsapp,
				"description": values.ticket_description,
				"screen_recording": screen_recording,

			},
			freeze: true,
			freeze_message: __("Creating ticket..."),
			callback: (r) => {
				if (!r.exc && r.message) {
					frappe.show_alert({
						indicator: "green",
						message: __("Ticket raised successfully"),
					});
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
		this.inUpload = false;

		genie.chunks = [];
		genie.blob = null;
		genie.blobURL = null;

		this.maxFileSizeInBytes = frappe.boot.genie_max_file_size * 1024 * 1024;
		this.sizeWarning = (frappe.boot.genie_max_file_size / 4) * 1024 * 1024;
		this.nextWarningSize = this.sizeWarning;
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
				this.checkFileSize();
			};
			this.recorder.onstop = this.handleStop;
			this.recorder.start(1000);
			console.log('Recording started');

			this.setIndicator("spinner-grow text-danger align-self-center mr-2");
			this.dialog.set_df_property("record_screen", "label", "Stop Recording");
			this.dialog.set_df_property("view_recording", "hidden", 1);
			this.dialog.set_df_property("clear_recording", "hidden", 1);
			frappe.show_alert({
				indicator: "green",
				message: __(`Screen recording has started. Please click on "Stop Recording" once you are done.`)
			})
		} else {
			console.warn('No stream available.');
			frappe.show_alert({
				indicator: "red",
				message: __("Error starting screen recording. Please try again.")
			});
		}
	}

	stopRecording() {
		this.recorder.stop();
		this.setIndicator();
		this.dialog.set_df_property("record_screen", "label", "Start Recording")
		this.dialog.set_df_property("view_recording", "hidden", 0);
		this.dialog.set_df_property("clear_recording", "hidden", 0);
		frappe.show_alert({
			indicator: "green",
			message: __(`Screen recording has stopped. Please click on "View Recording" to view the recording.`)
		})
	}

	checkFileSize() {
		const totalSize = genie.chunks.reduce((acc, chunk) => acc + chunk.size, 0);

		if (totalSize >= this.maxFileSizeInBytes) {
			frappe.show_alert({
				indicator: "red",
				message: __("Screen recording size has exceeded the maximum allowed size. Recording has been stopped.")
			});
			this.stopRecording();
			return;
		}


		if (totalSize >= this.nextWarningSize) {
			frappe.show_alert({
				indicator: "yellow",
				message: __(`Screen recording size has exceeded ${(totalSize / (1024 * 1024)).toFixed(1)}MB.`)
			});
			this.nextWarningSize += this.sizeWarning;
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
