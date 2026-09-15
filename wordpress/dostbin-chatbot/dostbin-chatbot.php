<?php
/**
 * Plugin Name: DOSTBin Chatbot
 * Description: Embeds the DOSTBin RAG chatbot. The Groq API key stays on the FastAPI server, not in WordPress.
 * Version: 1.0.0
 * Author: DOSTBin
 * License: GPL-2.0-or-later
 */

if (!defined('ABSPATH')) {
    exit;
}

function dostbin_chatbot_default_api_url() {
    return 'http://127.0.0.1:8000';
}

function dostbin_chatbot_api_url() {
    $url = get_option('dostbin_chatbot_api_url', dostbin_chatbot_default_api_url());
    $url = esc_url_raw(trim((string) $url));
    return untrailingslashit($url ?: dostbin_chatbot_default_api_url());
}

function dostbin_chatbot_add_settings_page() {
    add_options_page(
        'DOSTBin Chatbot',
        'DOSTBin Chatbot',
        'manage_options',
        'dostbin-chatbot',
        'dostbin_chatbot_render_settings_page'
    );
}
add_action('admin_menu', 'dostbin_chatbot_add_settings_page');

function dostbin_chatbot_register_settings() {
    register_setting('dostbin_chatbot_settings', 'dostbin_chatbot_api_url', array(
        'type' => 'string',
        'sanitize_callback' => 'esc_url_raw',
        'default' => dostbin_chatbot_default_api_url(),
    ));
}
add_action('admin_init', 'dostbin_chatbot_register_settings');

function dostbin_chatbot_render_settings_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    ?>
    <div class="wrap">
        <h1>DOSTBin Chatbot</h1>
        <p>Point this plugin at your FastAPI chatbot server. Do not put a Groq API key here.</p>
        <form method="post" action="options.php">
            <?php settings_fields('dostbin_chatbot_settings'); ?>
            <table class="form-table" role="presentation">
                <tr>
                    <th scope="row"><label for="dostbin_chatbot_api_url">Chatbot API URL</label></th>
                    <td>
                        <input
                            name="dostbin_chatbot_api_url"
                            id="dostbin_chatbot_api_url"
                            type="url"
                            class="regular-text"
                            value="<?php echo esc_attr(dostbin_chatbot_api_url()); ?>"
                            placeholder="https://chatbot.example.com"
                            required
                        />
                        <p class="description">Public URL of the FastAPI app, for example <code>https://chat.dostbin.com</code>.</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        <p>Add the chatbot to a page with the shortcode: <code>[dostbin_chat]</code></p>
    </div>
    <?php
}

function dostbin_chatbot_shortcode($atts) {
    $atts = shortcode_atts(array(
        'height' => '640',
    ), $atts, 'dostbin_chat');

    $api_url = dostbin_chatbot_api_url();
    $src = $api_url . '/embed';
    $height = absint($atts['height']);
    if ($height < 360) {
        $height = 640;
    }

    return sprintf(
        '<div class="dostbin-chatbot-embed"><iframe src="%1$s" title="DOSTBin Assistant" loading="lazy" referrerpolicy="no-referrer" style="width:100%%;height:%2$dpx;border:0;border-radius:16px;background:transparent;"></iframe></div>',
        esc_url($src),
        $height
    );
}
add_shortcode('dostbin_chat', 'dostbin_chatbot_shortcode');
