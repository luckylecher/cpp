;; Auther: JerryZhang
;; E-mail: chinajiezhang@gmail.com
;; Blog: http://www.zhangjiee.com

(add-to-list 'load-path "~/.emacs.d/lisp/")
;;(add-to-list 'load-path "~/.emacs.d/lisp/helm")
(add-to-list 'load-path "~/.emacs.d/lisp/window-numbering.el")
(add-to-list 'load-path "~/.emacs.d/lisp/highlight-symbol.el")
(add-to-list 'load-path "~/.emacs.d/lisp/expand-region.el")
(add-to-list 'load-path "~/.emacs.d/lisp/popup-el")
(add-to-list 'load-path "~/.emacs.d/lisp/auto-complete")
(add-to-list 'load-path "~/.emacs.d/lisp/auto-complete-c-headers")
(add-to-list 'load-path "~/.emacs.d/lisp/yasnippet")
(add-to-list 'load-path "~/.emacs.d/lisp/smex")
(add-to-list 'load-path "~/.emacs.d/lisp/lua-mode")
(add-to-list 'load-path "~/.emacs.d/lisp/web-mode")
(add-to-list 'load-path "~/.emacs.d/lisp/xcscope.el")
(add-to-list 'load-path "~/.emacs.d/lisp/ample-theme")

;;------------------------------------------------------------------------------
;; 基本设置(独立于插件)
;;------------------------------------------------------------------------------
(setq user-full-name "Lecher")
(setq user-mail-address "lecher.lc@alibaba-inc.com")

;; (display-time-mode 1)
;; (setq display-time-24hr-format t)
;; (setq display-time-day-and-date t)

(fset 'yes-or-no-p 'y-or-n-p)
(setq auto-save-default nil)
(setq inhibit-startup-message t)
(setq mouse-yank-at-point t)
(setq make-backup-files nil)
(setq create-lockfiles nil)
(column-number-mode t)

(setq-default indent-tabs-mode nil)
(setq-default tab-width 4)

;;------------------------------------------------------------------------------
;; 括号
;;------------------------------------------------------------------------------
(require 'electric)
(electric-indent-mode t)
;;(electric-pair-mode t)
(electric-layout-mode t)
(show-paren-mode t)

;;------------------------------------------------------------------------------
;; 外观
;;------------------------------------------------------------------------------
(global-visual-line-mode 1)

(setq linum-format "%3d|")
(global-linum-mode 2)
(global-set-key (kbd "M-s l") 'global-linum-mode)

(require 'fill-column-indicator)
;;(setq fci-rule-color "#333")
(setq fci-rule-color "#eee")
(setq fci-rule-column 80)
(define-globalized-minor-mode
  global-fci-mode fci-mode (lambda () (fci-mode 1)))
;;(global-fci-mode 1)

;; theme
;;(load-theme 'wombat)
(require 'ample-theme)

;;------------------------------------------------------------------------------
;; 打开文件，缓冲区切换优化
;;------------------------------------------------------------------------------
;; 使用 M-(1,2,3...9)窗口切换
(require 'window-numbering)
(setq window-numbering-assign-func
      (lambda () (when (equal (buffer-name) "*Calculator*") 9)))
(window-numbering-mode 1)

(require 'ido)
(ido-mode 1)

(require 'smex)
(smex-initialize)
(global-set-key (kbd "M-x") 'smex)
(global-set-key (kbd "M-X") 'smex-major-mode-commands)
;; This is your old M-x.
(global-set-key (kbd "C-c C-c M-x") 'execute-extended-command)

;;------------------------------------------------------------------------------
;; helm
;;------------------------------------------------------------------------------
;; (require 'helm)
;; (require 'helm-config)
;; (require 'helm-eshell)

;; (add-hook 'eshell-mode-hook
;;           #'(lambda ()
;;               (define-key eshell-mode-map (kbd "C-c C-l")  'helm-eshell-history)))

;; (global-set-key (kbd "C-c h") 'helm-command-prefix)
;; (define-key helm-map (kbd "<tab>") 'helm-execute-persistent-action) 
;; (define-key helm-map (kbd "C-i") 'helm-execute-persistent-action)
;; (define-key helm-map (kbd "C-z") 'helm-select-action)

;; (when (executable-find "curl")
;;   (setq helm-google-suggest-use-curl-p t))

;; (setq helm-split-window-in-side-p           t 
;;       helm-move-to-line-cycle-in-source     t
;;       helm-ff-search-library-in-sexp        t 
;;       helm-scroll-amount                    8 
;;       helm-ff-file-name-history-use-recentf t
;;       )

;; (global-set-key (kbd "M-x") 'helm-M-x)
;; (global-set-key (kbd "M-y") 'helm-show-kill-ring)
;; (global-set-key (kbd "C-x b") 'helm-mini)
;; (global-set-key (kbd "M-y") 'helm-show-kill-ring)
;; (global-set-key (kbd "C-c h o") 'helm-occur)
;; (setq helm-M-x-fuzzy-match t)
;; ;;(helm-autoresize-mode 1)
;; (helm-mode 1)

;;------------------------------------------------------------------------------
;; 相同符号高亮
;;------------------------------------------------------------------------------
(require 'highlight-symbol)
(global-set-key (kbd "M--") 'highlight-symbol-at-point)
(global-set-key (kbd "M-n") 'highlight-symbol-next)
(global-set-key (kbd "M-p") 'highlight-symbol-prev)

;;------------------------------------------------------------------------------
;; 自动补全
;;------------------------------------------------------------------------------
(require 'popup)

(require 'auto-complete)
(require 'auto-complete-config)
(add-to-list 'ac-dictionary-directories
             "~/.emacs.d/auto-complete/dict")
(ac-config-default)
(add-to-list 'ac-modes 'protobuf-mode)

;; (require 'yasnippet)
;; (yas-global-mode 1)

(defun my:ac-c-headers-init ()
  (require 'auto-complete-c-headers)
  (add-to-list 'ac-sources 'ac-source-c-headers)
  (add-to-list 'achead:include-directories '"/usr/lib/gcc/x86_64-redhat-linux/4.4.7/../../../../include/c++/4.4.7")
  (add-to-list 'achead:include-directories '"/usr/lib/gcc/x86_64-redhat-linux/4.4.7/../../../../include/c++/4.4.7/x86_64-redhat-linux")
  (add-to-list 'achead:include-directories '"/usr/lib/gcc/x86_64-redhat-linux/4.4.7/../../../../include/c++/4.4.7/backward")
  (add-to-list 'achead:include-directories '"/usr/local/include")
  (add-to-list 'achead:include-directories '"/usr/lib/gcc/x86_64-redhat-linux/4.4.7/include")
  (add-to-list 'achead:include-directories '"/usr/include"))

(add-hook 'c++-mode-hook 'my:ac-c-headers-init)
(add-hook 'c-mode-hook 'my:ac-c-headers-init)

;; -----------------------------------------------------------------------------
;; Google Protobuf file
;; -----------------------------------------------------------------------------
(require 'protobuf-mode)
(add-to-list 'auto-mode-alist '("\\.proto$" . protobuf-mode))

;; -----------------------------------------------------------------------------
;; YAML
;; -----------------------------------------------------------------------------
(require 'yaml-mode)
(add-to-list 'auto-mode-alist '("\\.yml$" . yaml-mode))
(add-to-list 'auto-mode-alist '("\\.yaml$" . yaml-mode))

;;------------------------------------------------------------------------------
;; Markdown
;;------------------------------------------------------------------------------
(autoload 'markdown-mode "~/.emacs.d/lisp/markdown-mode/markdown-mode.el"
  "Major mode for editing Markdown files" t)
(setq auto-mode-alist
      (cons '("\\.md" . markdown-mode) auto-mode-alist))
(setq auto-mode-alist
      (cons '("\\.markdown" . markdown-mode) auto-mode-alist))

;;------------------------------------------------------------------------------
;; lua mode
;;------------------------------------------------------------------------------
(autoload 'lua-mode "lua-mode" "lua editing mode. " t)
(add-to-list 'auto-mode-alist '("\\.lua$" . lua-mode))
(add-to-list 'interpreter-mode-alist '("lua" . lua-mode))

;;------------------------------------------------------------------------------
;; web-mode
;;------------------------------------------------------------------------------
(require 'web-mode)
(add-to-list 'auto-mode-alist '("\\.html?\\'" . web-mode))
(add-to-list 'auto-mode-alist '("\\.xml?\\'" . web-mode))
(setq web-mode-enable-current-element-highlight t)

;;------------------------------------------------------------------------------
;; Python
;;------------------------------------------------------------------------------
(require 'python-mode)

(add-hook 'python-mode-hook
          (lambda ()
            (set (make-local-variable 'compile-command)
                 (format "python %s" (file-name-nondirectory buffer-file-name)))))

;;------------------------------------------------------------------------------
;; expand-region
;;------------------------------------------------------------------------------
(require 'expand-region)
(global-set-key (kbd "M-m") 'er/expand-region)
(global-set-key (kbd "M-s s") 'er/mark-symbol)
(global-set-key (kbd "M-s p") 'er/mark-outside-pairs)
(global-set-key (kbd "M-s P") 'er/mark-inside-pairs)
(global-set-key (kbd "M-s q") 'er/mark-outside-quotes)
(global-set-key (kbd "M-s Q") 'er/mark-inside-quotes)
(global-set-key (kbd "M-s m") 'er/mark-comment)
(global-set-key (kbd "M-s f") 'er/mark-defun)

;;------------------------------------------------------------------------------
;; scheme
;;------------------------------------------------------------------------------
(require 'cmuscheme)

(defun kh/get-scheme-proc-create ()
  "Create one scheme process if no one is created."
  (unless (and scheme-buffer
               (get-buffer scheme-buffer)
               (comint-check-proc scheme-buffer))
    (save-window-excursion
      (run-scheme scheme-program-name))))

(defun kh/scheme-send-last-sexp ()
  "A replacement of original `scheme-send-last-sexp':
1. check if scheme process exists, otherwise create one
2. make sure the frame is splitted into two windows, current one is the scheme
   source code window, the other one is the scheme process window
3. run `scheme-send-last-sexp'

PS: this function is inspired by Wang Yin."
  (interactive)
  (kh/get-scheme-proc-create)
  (cond ((= 2 (count-windows))
         (other-window 1)
         (unless (string= (buffer-name)
                          scheme-buffer)
           (switch-to-buffer scheme-buffer))
         (other-window 1))
        (t
         (delete-other-windows)
         (split-window-vertically (floor (* 0.68 (window-height))))
         (other-window 1)
         (switch-to-buffer scheme-buffer)
         (other-window 1)))
  (scheme-send-last-sexp))

(setq scheme-program-name "mit-scheme")

(defun kh/add-hook (hooks funcs &optional append local)
  "More general definition of function add-hook."
  (unless (listp hooks)
    (setq hooks (list hooks)))
  (unless (listp funcs)
    (setq funcs (list funcs)))
  (dolist (hook hooks)
    (dolist (func funcs)
      (add-hook hook func append local))))

(kh/add-hook '(scheme-mode-hook)
             '((lambda ()
                 (local-set-key (kbd "C-x C-e") 'kh/scheme-send-last-sexp))))

;;------------------------------------------------------------------------------
;;   C/C++
;;------------------------------------------------------------------------------
(global-set-key [(f9)] 'ff-find-other-file)
(global-set-key [(f12)] 'semantic-mode)

(require 'xcscope)
(cscope-setup)

(setq tab-stop-list ())
(loop for x downfrom 40 to 1 do
      (setq tab-stop-list (cons (* x 4) tab-stop-list)))

(defconst my-c-style
  '(
    (c-tab-always-indent        . t)
    (c-hanging-braces-alist     . ((substatement-open after)
                                   (brace-list-open)))
    (c-hanging-colons-alist     . ((member-init-intro before)
                                   (inher-intro)'
                                   (label after)
                                   (acecss-label after)))
    (c-cleanup-list             . (scope-operator
                                   empty-defun-braces
                                   defun-close-semi))
    (c-offsets-alist            . ((arglist-close . c-lineup-arglist)
                                   (case-label . 4)
                                   (substatement-open . 0)
                                   (block-open        . 0)
                                   (knr-argdecl-intro . -)
                                   ;;(innamespace . -)
                                   (inline-open . 0)
                                   (inher-cont . c-lineup-multi-inher)
                                   (arglist-cont-nonempty . +)
                                   (template-args-cont . + )))
    (c-echo-syntactic-information-p . t)
    )
  "My C Programming Style")

;; offset customizations not in my-c-style
(setq c-offsets-alist '((member-init-intro . ++)))

;; Customizations for all modes in CC Mode.
(defun my-c-mode-common-hook ()
  ;; add my personal style and set it for the current buffer
  (c-add-style "PERSONAL" my-c-style t)
  ;; other customizations
  (setq tab-width 4
        indent-tabs-mode nil)
  ;; we like auto-newline and hungry-delete
  ;; (c-toggle-auto-hungry-state 1)
  ;; key bindings for all supported languages.  We can put these in
  ;; c-mode-base-map because c-mode-map, c++-mode-map, objc-mode-map,
  ;; java-mode-map, idl-mode-map, and pike-mode-map inherit from it.
  )
(add-hook 'c-mode-common-hook 'my-c-mode-common-hook)
(add-hook 'c-mode-hook 'hs-minor-mode)
(add-to-list 'auto-mode-alist '("\\.h\\'" . c++-mode))

(add-hook 'c++-mode-hook
          (lambda ()
            (set (make-local-variable 'compile-command)
                 (format "make -k -j4 -C "))))

;; http://stackoverflow.com/questions/14668744/emacs-indent-for-c-class-method
(defun vlad-cc-style()
  (c-set-offset 'inline-open '0)
  )
(add-hook 'c++-mode-hook 'vlad-cc-style)

;;------------------------------------------------------------------------------
;; 其他快捷键定制
;;------------------------------------------------------------------------------
(defun align-to-equals (begin end)
  "Align region to equal signs"
  (interactive "r")
  (align-regexp begin end "\\(\\s-*\\)=" 1 1 ))
(global-set-key (kbd "C-c a =") 'align-to-equals)

(defun clear-eshell-buffer ()
  (interactive)
  (let ((inhibit-read-only t))
    (delete-region (point-min) (point-max))))
(global-set-key (kbd "C-c l") 'clear-eshell-buffer)
(global-set-key (kbd "C-c e") 'eshell)
(global-unset-key (kbd "C-z"))

(global-set-key [(f5)] 'compile)

(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(custom-safe-themes
   (quote
    ("7fbb8d064286706fb1e319c9d3c0a8eafc2efe6b19380aae9734c228b05350ae" default)))
 '(save-place t nil (saveplace))
 )
