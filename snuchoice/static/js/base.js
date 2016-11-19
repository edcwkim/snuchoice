function parseIntThenAdd($obj, x) {
  $obj.each(function() {
    var newInt = +$(this).text().replace(",", "") + x;
    return $(this).text(newInt.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","));
  });
}

$(function() {
  $('[data-toggle="tooltip"]').tooltip();

  $(".owl-carousel").owlCarousel({
    items: 1,
    margin: 16,
    loop: true,
    center: true,
    stagePadding: 16,
    autoplay: true,
    autoplayTimeout: 8000,
    autoplayHoverPause: true,
    autoHeight: true,
    dotsContainer: ".owl-dots"
  });

  $(".home .feed .question .vote").click(function(e) {
    e.preventDefault();
    if ($("body").hasClass("authenticated")) {
      var $wrapper = $(this).closest(".vote-wrapper"),
          $progress = $wrapper.closest(".question").find(".progress"),
          current_percent = parseFloat($progress.find(".character")[0].style.left),
          threshold = +$progress.data("threshold"), next_percent;
      $wrapper.toggleClass("voted");
      if ($wrapper.hasClass("voted")) {
        parseIntThenAdd($wrapper.find(".count"), 1);
        next_percent = current_percent + 100 / threshold;
        if (next_percent <= 100) {
          $progress.find(".character").css("left", next_percent + "%");
          $progress.find(".bar span").css("width", next_percent + "%");
        }
      }
      else {
        parseIntThenAdd($wrapper.find(".count"), -1);
        next_percent = current_percent - 100 / threshold;
        if (next_percent >= 0) {
          $progress.find(".character").css("left", next_percent + "%");
          $progress.find(".bar span").css("width", next_percent + "%");
        }
      }
      $.ajax({
        type: "POST",
        url: $wrapper.attr("action"),
        data: $wrapper.serialize(),
        dataType: "json",
        success: function(data) {
          if (data.redirect)
            window.location.replace(login_url);
        },
        error: function() {
          current_percent = parseFloat($progress.find(".character")[0].style.left);
          $wrapper.toggleClass("voted");
          if ($wrapper.hasClass("voted")) {
            parseIntThenAdd($wrapper.find(".count"), 1);
            next_percent = current_percent + 100 / threshold;
            if (next_percent <= 100) {
              $progress.find(".character").css("left", next_percent + "%");
              $progress.find(".bar span").css("width", next_percent + "%");
            }
          }
          else {
            parseIntThenAdd($wrapper.find(".count"), -1);
            next_percent = current_percent - 100 / threshold;
            if (next_percent >= 0) {
              $progress.find(".character").css("left", next_percent + "%");
              $progress.find(".bar span").css("width", next_percent + "%");
            }
          }
        }
      });
    }
    else {
      r = confirm("공론화에 참여하기 위해서는 구성원 인증을 하셔야 합니다.");
      if (r === true)
        window.location.replace(login_url);
    }
  });

  $(".question-detail .action .vote-wrapper .vote").click(function(e) {
    e.preventDefault();
    if ($("body").hasClass("authenticated")) {
      var $wrapper = $(this).closest(".vote-wrapper"),
          $progress = $wrapper.closest(".question-detail").find(".progress"),
          current_percent = parseFloat($progress.find(".character")[0].style.left),
          threshold = +$progress.data("threshold"), next_percent;
      $(this).closest(".vote-wrapper").toggleClass("voted");
      if ($(this).closest(".vote-wrapper").hasClass("voted")) {
        parseIntThenAdd($(".like-count"), 1);
        parseIntThenAdd($(".likes-left"), -1);
        next_percent = current_percent + 100 / threshold;
        if (next_percent <= 100) {
          $progress.find(".character").css("left", next_percent + "%");
          $progress.find(".bar span").css("width", next_percent + "%");
        }
      }
      else {
        parseIntThenAdd($(".like-count"), -1);
        parseIntThenAdd($(".likes-left"), 1);
        next_percent = current_percent - 100 / threshold;
        if (next_percent >= 0) {
          $progress.find(".character").css("left", next_percent + "%");
          $progress.find(".bar span").css("width", next_percent + "%");
        }
      }
      $.ajax({
        type: "POST",
        url: $wrapper.attr("action"),
        data: $wrapper.serialize(),
        dataType: "json",
        success: function(data) {
          if (data.redirect)
            window.location.replace(login_url);
        },
        error: function() {
          current_percent = parseFloat($progress.find(".character")[0].style.left);
          $wrapper.toggleClass("voted");
          if ($wrapper.hasClass("voted")) {
            parseIntThenAdd($(".like-count"), 1);
            parseIntThenAdd($(".likes-left"), -1);
            next_percent = current_percent + 100 / threshold;
            if (next_percent <= 100) {
              $progress.find(".character").css("left", next_percent + "%");
              $progress.find(".bar span").css("width", next_percent + "%");
            }
          }
          else {
            parseIntThenAdd($(".like-count"), -1);
            parseIntThenAdd($(".likes-left"), 1);
            next_percent = current_percent - 100 / threshold;
            if (next_percent >= 0) {
              $progress.find(".character").css("left", next_percent + "%");
              $progress.find(".bar span").css("width", next_percent + "%");
            }
          }
        }
      });
    }
    else {
      r = confirm("공론화에 참여하기 위해서는 구성원 인증을 하셔야 합니다.");
      if (r === true)
        window.location.replace(login_url);
    }
  });

  var $college = $(".question-detail .answers .election-head.colleges .college.selected");
  $(".question-detail .answers [data-college-id=" + $college.data("id") + "]").addClass("show");

  $(".question-detail .answers .election-head.colleges .college").click(function(e) {
    $(".question-detail .answers .election-head.colleges .college").removeClass("selected");
    $(this).addClass("selected");
    $(".question-detail .answers [data-college-id]").removeClass("show");
    $(".question-detail .answers [data-college-id=" + $(this).data("id") + "]").addClass("show");
    if (!$(".question-detail .answers [data-college-id=" + $(this).data("id") + "]").length) {
      $('.question-detail .answers .empty').show();
    }
    else {
      $('.question-detail .answers .empty').hide();
    }
  });

  $(document).ready(function() {
    if (!$(".question-detail .answers [data-college-id=1]").length) {
      $('.question-detail .answers .empty').show();
    }
    else {
      $('.question-detail .answers .empty').hide();
    }
  });

  $(".question-edit .select-chong input").change(function() {
    if (this.value == "Y")
      $(".question-edit .select-college").addClass("disabled")
                                         .find("input").attr("disabled", true)
                                                       .attr("required", false);
    else
      $(".question-edit .select-college").removeClass("disabled")
                                         .find("input").attr("disabled", false)
                                                       .attr("required", true);
  });

  var emailConfirmFormSubmitting = false;
  $('#emailConfirmForm').on('submit', function(e) {
    e.preventDefault();

    // 중복 서브밋 방지
    if (emailConfirmFormSubmitting)
      return false;
    emailConfirmFormSubmitting = true;

    var that = $(this),
        url = that.attr('action');
        email = that.find('input[name=email]').val();
        btn = that.find('button[type=submit]');

    btn.button('loading');
    $.post(url, {email: email})
      .done(function(data) {
        btn.button('reset');
        if (data.success) {
          var r = confirm("인증 메일이 발송되었습니다. 마이스누 메일함으로 이동하시겠습니까?");
          if (r === true)
            setTimeout(function() {
              window.location.replace("https://mail.snu.ac.kr/");
            }, 2000);
          else
            alert("메일을 확인해 주세요.");
        }
        else {
          that.find('#emailInputWrapper').html(data.html);
        }
      })
      .fail(function(jqXHR) {
        btn.button('reset');
        alert('오류가 발생했습니다. 다시 시도해 주세요.\n오류가 지속될 경우 contact@snuchoice.com으로 연락 부탁드립니다.');
      })
      .always(function() {
        emailConfirmFormSubmitting = false;
      });
  });
});
