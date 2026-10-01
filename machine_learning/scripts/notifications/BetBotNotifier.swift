// A stable app identity makes notification permission explicit and inspectable.
// Built locally on macOS; no binaries or signing credentials belong in Git.
import AppKit
import UserNotifications

final class Notifier: NSObject, NSApplicationDelegate, UNUserNotificationCenterDelegate {
    private let arguments = Array(CommandLine.arguments.dropFirst())
    private let center = UNUserNotificationCenter.current()

    private func finish(_ message: String, code: Int32 = 0) {
        print(message)
        // `open` does not forward app stdout or its exit code, so callers pass a
        // unique result file and inspect it after the app exits.
        if let index = arguments.firstIndex(of: "--result"), arguments.count > index + 1 {
            do {
                try "\(code): \(message)\n".write(
                    toFile: arguments[index + 1], atomically: true, encoding: .utf8
                )
            } catch {
                fputs("Cannot write notification result: \(error)\n", stderr)
            }
        }
        DispatchQueue.main.async { NSApplication.shared.terminate(nil) }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        center.delegate = self
        // Bound helper lifetime even when macOS does not answer. Daily updates
        // never request authorization; only the explicit setup command does.
        DispatchQueue.main.asyncAfter(deadline: .now() + 30) {
            self.finish("Notification service did not finish within 30 seconds", code: 1)
        }
        if arguments.contains("--authorize") {
            center.requestAuthorization(options: [.alert, .sound]) { granted, error in
                if let error = error {
                    self.finish("Authorization failed: \(error)", code: 1)
                } else {
                    self.finish(granted ? "Notifications authorized" : "Notifications denied", code: granted ? 0 : 1)
                }
            }
        } else {
            center.getNotificationSettings { settings in
                guard settings.authorizationStatus == .authorized else {
                    self.finish("Notifications are not authorized; run the notifier setup command", code: 1)
                    return
                }
                if self.arguments.contains("--status") {
                    self.finish("Notifications authorized; alert setting: \(settings.alertSetting.rawValue)")
                    return
                }
                guard let index = self.arguments.firstIndex(of: "--message"), self.arguments.count > index + 1 else {
                    self.finish("Missing --message", code: 1)
                    return
                }
                let content = UNMutableNotificationContent()
                content.title = "BetBot MLB update"
                content.body = self.arguments[index + 1]
                content.sound = .default
                let request = UNNotificationRequest(
                    identifier: UUID().uuidString, content: content,
                    trigger: UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
                )
                self.center.add(request) { error in
                    if let error = error {
                        self.finish("Notification submission failed: \(error)", code: 1)
                    } else {
                        self.finish("Notification accepted by macOS; visibility still requires observation")
                    }
                }
            }
        }
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter, willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .list, .sound])
    }
}

let app = NSApplication.shared
let delegate = Notifier()
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
